const DEFAULT_CANDIDATE_LEVEL_LABELS = ["IN →", "LEVEL"];
const DEFAULT_CANDIDATE_INVALIDATION_LABELS = ["OUT →", "INVALIDATION"];
const DEFAULT_OPPORTUNITY_LABELS = [
  "SURFACED",
  "QUALIFIED",
  "SETUPS FOUND",
  "WATCHLIST",
  "REJECTED",
  "PRIMARY REJECTION"
];

/**
 * Build the browser-side probe as a self-contained expression. The probe records
 * raw facts only; FAIL/WARNING/INFORMATIONAL policy belongs in checks.mjs.
 */
export function buildProbeExpression(contract = {}) {
  const payload = JSON.stringify({
    selectors: contract.selectors || {},
    contextKeys: contract.contextKeys || [],
    surfaceKeys: contract.surfaceKeys || [],
    candidateLevelLabels:
      contract.candidateLevelLabels || DEFAULT_CANDIDATE_LEVEL_LABELS,
    candidateInvalidationLabels:
      contract.candidateInvalidationLabels || DEFAULT_CANDIDATE_INVALIDATION_LABELS,
    opportunityLabels: contract.opportunityLabels || DEFAULT_OPPORTUNITY_LABELS
  });

  return `
    (() => {
      const contract = ${payload};
      const round = (value) => Number.isFinite(value)
        ? Math.round(value * 10) / 10
        : null;
      const one = (selector) => selector ? document.querySelector(selector) : null;
      const rectOf = (element) => {
        if (!element) return null;
        const rect = element.getBoundingClientRect();
        return {
          top: round(rect.top),
          right: round(rect.right),
          bottom: round(rect.bottom),
          left: round(rect.left),
          width: round(rect.width),
          height: round(rect.height),
          pageTop: round(rect.top + scrollY),
          pageBottom: round(rect.bottom + scrollY)
        };
      };
      const textRectOf = (element) => {
        if (!element || !element.firstChild) return null;
        const range = document.createRange();
        range.selectNodeContents(element);
        const rects = Array.from(range.getClientRects()).filter((rect) =>
          rect.width > 0 && rect.height > 0
        );
        if (!rects.length) return null;
        return {
          top: round(Math.min(...rects.map((rect) => rect.top))),
          right: round(Math.max(...rects.map((rect) => rect.right))),
          bottom: round(Math.max(...rects.map((rect) => rect.bottom))),
          left: round(Math.min(...rects.map((rect) => rect.left))),
          lineBoxCount: rects.length
        };
      };
      const ancestorState = (element) => {
        const hiddenBy = [];
        const clippedBy = [];
        const elementRect = element ? element.getBoundingClientRect() : null;
        let current = element ? element.parentElement : null;
        while (current) {
          const style = getComputedStyle(current);
          const opacity = Number.parseFloat(style.opacity);
          if (style.display === "none" || style.visibility === "hidden" ||
              style.visibility === "collapse" || opacity === 0) {
            hiddenBy.push(current.id || current.className || current.tagName);
          }
          if (elementRect) {
            const rect = current.getBoundingClientRect();
            const clipsX = ["hidden", "clip"].includes(style.overflowX) &&
              (elementRect.left < rect.left - 1 || elementRect.right > rect.right + 1);
            const clipsY = ["hidden", "clip"].includes(style.overflowY) &&
              (elementRect.top < rect.top - 1 || elementRect.bottom > rect.bottom + 1);
            if (clipsX || clipsY) {
              clippedBy.push({
                ancestor: current.id || current.className || current.tagName,
                axis: clipsX && clipsY ? "both" : clipsX ? "x" : "y"
              });
            }
          }
          current = current.parentElement;
        }
        return { hiddenBy, clippedBy };
      };
      const record = (key, selector, element) => {
        if (!element) {
          return { key, selector, present: false };
        }
        const style = getComputedStyle(element);
        const rect = rectOf(element);
        const textRect = textRectOf(element);
        const opacity = Number.parseFloat(style.opacity);
        const ancestors = ancestorState(element);
        const zeroSize = !rect || rect.width <= 0 || rect.height <= 0;
        const directlyHidden = style.display === "none" ||
          style.visibility === "hidden" ||
          style.visibility === "collapse" ||
          opacity <= 0.001 ||
          element.hidden === true;
        const scrollableY = ["auto", "scroll"].includes(style.overflowY);
        const scrollableX = ["auto", "scroll"].includes(style.overflowX);
        const horizontalContentOverflow =
          element.clientWidth > 0 && element.scrollWidth - element.clientWidth > 1;
        const verticalContentOverflow =
          element.clientHeight > 0 && element.scrollHeight - element.clientHeight > 1;
        const textExitsBoxX = Boolean(textRect && rect &&
          (textRect.left < rect.left - 1 || textRect.right > rect.right + 1));
        const textExitsBoxY = Boolean(textRect && rect &&
          (textRect.top < rect.top - 1 || textRect.bottom > rect.bottom + 1));
        return {
          key,
          selector,
          present: true,
          text: (element.innerText || element.textContent || "").trim(),
          rect,
          textRect,
          clientWidth: element.clientWidth,
          scrollWidth: element.scrollWidth,
          clientHeight: element.clientHeight,
          scrollHeight: element.scrollHeight,
          display: style.display,
          visibility: style.visibility,
          opacity: Number.isFinite(opacity) ? opacity : null,
          overflowX: style.overflowX,
          overflowY: style.overflowY,
          whiteSpace: style.whiteSpace,
          lineHeight: style.lineHeight,
          zeroSize,
          directlyHidden,
          hiddenByAncestor: ancestors.hiddenBy,
          clippedByAncestor: ancestors.clippedBy,
          horizontalContentOverflow,
          verticalContentOverflow,
          nonScrollHorizontalOverflow: horizontalContentOverflow && !scrollableX,
          nonScrollVerticalOverflow: verticalContentOverflow && !scrollableY,
          textExitsBoxX,
          textExitsBoxY,
          wraps: Boolean(textRect && textRect.lineBoxCount > 1)
        };
      };
      const findLabelValue = (within, labels) => {
        if (!within) return null;
        const normalized = labels.map((label) => label.toUpperCase());
        const candidates = Array.from(within.querySelectorAll(".label"));
        const label = candidates.find((element) =>
          normalized.includes((element.innerText || element.textContent || "").trim().toUpperCase())
        );
        return label ? label.nextElementSibling : null;
      };
      const selectors = contract.selectors;
      const nodes = Object.fromEntries(
        Object.entries(selectors).map(([key, selector]) => [key, one(selector)])
      );
      const elements = Object.fromEntries(
        Object.entries(selectors).map(([key, selector]) => [
          key,
          record(key, selector, nodes[key])
        ])
      );

      const candidate = nodes.candidate || one("#candidate-board");
      const candidateCards = candidate
        ? Array.from(candidate.querySelectorAll(".candidate-card"))
        : [];
      const candidateLevel = findLabelValue(candidate, contract.candidateLevelLabels);
      const candidateInvalidation = findLabelValue(
        candidate,
        contract.candidateInvalidationLabels
      );
      elements.candidateLevel = record(
        "candidateLevel",
        "candidate label value: " + contract.candidateLevelLabels.join("|"),
        candidateLevel
      );
      elements.candidateInvalidation = record(
        "candidateInvalidation",
        "candidate label value: " + contract.candidateInvalidationLabels.join("|"),
        candidateInvalidation
      );

      const opportunity = nodes.opportunity || one("#opportunity-survival");
      const opportunityValues = {};
      for (const label of contract.opportunityLabels) {
        const value = findLabelValue(opportunity, [label]);
        opportunityValues[label] = record(
          "opportunity:" + label,
          "opportunity label value: " + label,
          value
        );
      }

      const presentSurfaceKeys = contract.surfaceKeys.filter((key) => nodes[key]);
      presentSurfaceKeys.sort((left, right) => {
        const position = nodes[left].compareDocumentPosition(nodes[right]);
        return position & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
      });
      const surfaces = presentSurfaceKeys.map((key) => {
        const measurement = elements[key];
        const rect = measurement.rect;
        const rendered = measurement.present && !measurement.directlyHidden &&
          !measurement.zeroSize && measurement.hiddenByAncestor.length === 0;
        return {
          key,
          top: rect ? rect.pageTop : null,
          bottom: rect ? rect.pageBottom : null,
          height: rect ? rect.height : null,
          intersectsInitialFold: Boolean(rendered && rect && rect.top < innerHeight && rect.bottom > 0),
          fullyAboveFold: Boolean(rendered && rect && rect.top >= 0 && rect.bottom <= innerHeight)
        };
      });

      const firstContextKey = presentSurfaceKeys.find((key) =>
        contract.contextKeys.includes(key)
      ) || null;
      const root = nodes.root || document.body;
      const rootRect = rectOf(root);
      const opportunityRect = rectOf(opportunity);
      const candidateRect = rectOf(candidate);
      const candidateIdentity = nodes.candidateIdentity ||
        one("#candidate-board .candidate-card .card-header");
      const candidateIdentityRect = rectOf(candidateIdentity);
      const candidateLevelRect = rectOf(candidateLevel);
      const candidateInvalidationRect = rectOf(candidateInvalidation);
      const contextRect = firstContextKey ? rectOf(nodes[firstContextKey]) : null;
      const gexRect = rectOf(nodes.gex || one("#gex-context"));
      const opportunityIndex = presentSurfaceKeys.indexOf("opportunity");
      const candidateIndex = presentSurfaceKeys.indexOf("candidate");
      const surfacesBetweenOpportunityAndCandidate =
        opportunityIndex >= 0 && candidateIndex >= 0
          ? Math.max(0, Math.abs(candidateIndex - opportunityIndex) - 1)
          : null;
      const candidateBeforeContext = candidate && firstContextKey
        ? Boolean(candidate.compareDocumentPosition(nodes[firstContextKey]) & Node.DOCUMENT_POSITION_FOLLOWING)
        : null;
      const gexExposedSpace = gexRect
        ? Math.max(0, Math.min(gexRect.bottom, innerHeight) - Math.max(gexRect.top, 0))
        : 0;

      const rootChildren = Array.from(root.children || [])
        .filter((element) => element.id)
        .map((element) => element.id);
      const boundary = one('[data-lab-key="boundary"]');
      const boundaryStyle = boundary ? getComputedStyle(boundary) : null;

      return {
        viewport: {
          width: innerWidth,
          height: innerHeight,
          devicePixelRatio,
          rootFontSize: getComputedStyle(document.documentElement).fontSize
        },
        page: {
          clientWidth: document.documentElement.clientWidth,
          scrollWidth: document.documentElement.scrollWidth,
          overflowX: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
          clientHeight: document.documentElement.clientHeight,
          scrollHeight: document.documentElement.scrollHeight
        },
        elements,
        candidateStats: {
          cardCount: candidateCards.length,
          cardIds: candidateCards.map((element) => element.id || null)
        },
        opportunityValues,
        text: {
          body: (document.body.innerText || "").trim(),
          byKey: Object.fromEntries(Object.entries(elements).map(([key, value]) => [key, value.text || ""]))
        },
        dom: {
          topLevelIds: rootChildren,
          surfaceOrder: presentSurfaceKeys
        },
        geometry: {
          rootTop: rootRect ? rootRect.pageTop : null,
          firstZoneHeight: rootRect && opportunityRect
            ? round(opportunityRect.pageBottom - rootRect.pageTop)
            : null,
          candidateY: candidateRect ? candidateRect.pageTop : null,
          candidateIdentityY: candidateIdentityRect ? candidateIdentityRect.pageTop : null,
          candidateLevelY: candidateLevelRect ? candidateLevelRect.pageTop : null,
          candidateInvalidationY: candidateInvalidationRect ? candidateInvalidationRect.pageTop : null,
          contextKey: firstContextKey,
          contextY: contextRect ? contextRect.pageTop : null,
          gexY: gexRect ? gexRect.pageTop : null,
          gexHeight: gexRect ? gexRect.height : null,
          gexExposedSpace: round(gexExposedSpace),
          opportunityToCandidateGap: opportunityRect && candidateRect
            ? round(candidateRect.pageTop - opportunityRect.pageBottom)
            : null,
          surfacesBetweenOpportunityAndCandidate,
          opportunityCandidateAdjacent: surfacesBetweenOpportunityAndCandidate === 0,
          candidateBeforeContext,
          candidateWrapperPresent: Boolean(candidate),
          opportunityPresent: Boolean(opportunity)
        },
        fold: {
          intersecting: surfaces.filter((surface) => surface.intersectsInitialFold).map((surface) => surface.key),
          fullyAbove: surfaces.filter((surface) => surface.fullyAboveFold).map((surface) => surface.key)
        },
        boundary: boundary ? {
          rect: rectOf(boundary),
          marker: boundaryStyle.getPropertyValue("--lab-boundary").trim(),
          text: (boundary.innerText || boundary.textContent || "").trim()
        } : null
      };
    })()
  `;
}
