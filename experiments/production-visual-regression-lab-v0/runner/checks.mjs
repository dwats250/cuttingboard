const HIDDEN_REASON_KEYS = [
  "directlyHidden",
  "zeroSize"
];

function expectationIsPresent(value) {
  return value === true || value === "present" || value === "visible";
}

function expectationIsAbsent(value) {
  return value === false || value === "absent";
}

function messageList(entries) {
  return entries.map((entry) => entry.message);
}

/**
 * Classify one raw browser observation against one explicit fixture contract.
 * A check carries the policy severity even when it passes; `status` records the
 * observed result. INFORMATIONAL checks never promote the case verdict.
 */
export function classifyObservation(raw, fixture, defaults = {}) {
  const expected = fixture.expected || {};
  const checks = [];
  const add = (id, severity, failed, message, evidence = undefined) => {
    checks.push({
      id,
      severity,
      status: failed ? "FAIL" : "PASS",
      message,
      ...(evidence === undefined ? {} : { evidence })
    });
  };

  const pageOverflow = Number(raw.page?.overflowX || 0);
  add(
    "page-horizontal-overflow",
    "FAIL",
    pageOverflow > 1,
    pageOverflow > 1
      ? `horizontal page overflow: ${pageOverflow}px`
      : "no horizontal page overflow",
    { overflowPx: pageOverflow }
  );

  for (const [key, expectation] of Object.entries(expected.presence || {})) {
    const measurement = raw.elements?.[key] || { present: false };
    if (expectationIsPresent(expectation)) {
      add(
        `presence:${key}`,
        "FAIL",
        !measurement.present,
        measurement.present
          ? `${key} present as expected`
          : `missing expected element: ${key}`
      );
    } else if (expectationIsAbsent(expectation)) {
      add(
        `absence:${key}`,
        "FAIL",
        measurement.present,
        measurement.present
          ? `unexpected element present: ${key}`
          : `${key} absent as expected`
      );
    }
  }

  const candidateExpected = expected.candidate || {};
  const candidateCardCount = Number(raw.candidateStats?.cardCount || 0);
  if (Number.isInteger(candidateExpected.minimumCards)) {
    const minimumCards = candidateExpected.minimumCards;
    add(
      "candidate-minimum-card-count",
      "FAIL",
      candidateCardCount < minimumCards,
      candidateCardCount < minimumCards
        ? `candidate card count ${candidateCardCount} is below required minimum ${minimumCards}`
        : `candidate card count ${candidateCardCount} meets minimum ${minimumCards}`,
      { actual: candidateCardCount, minimum: minimumCards }
    );
  }
  if (Number.isInteger(candidateExpected.maximumCards)) {
    const maximumCards = candidateExpected.maximumCards;
    add(
      "candidate-maximum-card-count",
      "FAIL",
      candidateCardCount > maximumCards,
      candidateCardCount > maximumCards
        ? `candidate card count ${candidateCardCount} exceeds maximum ${maximumCards}`
        : `candidate card count ${candidateCardCount} is within maximum ${maximumCards}`,
      { actual: candidateCardCount, maximum: maximumCards }
    );
  }
  const candidateFields = {
    identity: "candidateIdentity",
    level: "candidateLevel",
    invalidation: "candidateInvalidation"
  };
  for (const [field, key] of Object.entries(candidateFields)) {
    if (!(field in candidateExpected)) continue;
    const measurement = raw.elements?.[key] || { present: false };
    const shouldExist = Boolean(candidateExpected[field]);
    add(
      `candidate-${field}`,
      "FAIL",
      shouldExist ? !measurement.present : measurement.present,
      shouldExist
        ? measurement.present
          ? `candidate ${field} present`
          : `candidate ${field} unexpectedly absent`
        : measurement.present
          ? `candidate ${field} fabricated when absent was expected`
          : `candidate ${field} absent as expected`
    );
  }

  const criticalKeys = new Set([
    ...(defaults.criticalKeys || []),
    ...(expected.criticalKeys || [])
  ]);
  for (const [field, key] of Object.entries(candidateFields)) {
    if (candidateExpected[field]) criticalKeys.add(key);
  }

  const checkCriticalMeasurement = (key, measurement) => {
    if (!measurement?.present) return;
    const hidden = HIDDEN_REASON_KEYS.some((reason) => measurement[reason]) ||
      (measurement.hiddenByAncestor || []).length > 0 ||
      Number(measurement.opacity) <= 0.001;
    add(
      `critical-visible:${key}`,
      "FAIL",
      hidden,
      hidden
        ? `critical element hidden or zero-sized: ${key}`
        : `critical element visible: ${key}`,
      {
        display: measurement.display,
        visibility: measurement.visibility,
        opacity: measurement.opacity,
        rect: measurement.rect,
        hiddenByAncestor: measurement.hiddenByAncestor || []
      }
    );

    const textBoundsAreAuthoritative =
      key.startsWith("opportunity:") ||
      [
        "candidateIdentity", "candidateLevel", "candidateInvalidation",
        "provenance", "qualifier", "staleness"
      ].includes(key);
    const ownHorizontalClip = Boolean(
      measurement.nonScrollHorizontalOverflow &&
      ["hidden", "clip"].includes(String(measurement.overflowX).toLowerCase())
    );
    const horizontalClip = Boolean(
      ownHorizontalClip ||
      (textBoundsAreAuthoritative && measurement.textExitsBoxX) ||
      (measurement.clippedByAncestor || []).some((item) =>
        item.axis === "x" || item.axis === "both"
      )
    );
    add(
      `critical-horizontal-clipping:${key}`,
      "FAIL",
      horizontalClip,
      horizontalClip
        ? `critical content clips horizontally: ${key}`
        : `critical content fits horizontally: ${key}`,
      {
        clientWidth: measurement.clientWidth,
        scrollWidth: measurement.scrollWidth,
        textExitsBoxX: measurement.textExitsBoxX,
        clippedByAncestor: measurement.clippedByAncestor || []
      }
    );

    const verticalClip = Boolean(
      measurement.nonScrollVerticalOverflow ||
      (textBoundsAreAuthoritative && measurement.textExitsBoxY) ||
      (measurement.clippedByAncestor || []).some((item) =>
        item.axis === "y" || item.axis === "both"
      )
    );
    add(
      `critical-vertical-clipping:${key}`,
      "FAIL",
      verticalClip,
      verticalClip
        ? `critical content clips vertically: ${key}`
        : `critical content fits vertically: ${key}`,
      {
        clientHeight: measurement.clientHeight,
        scrollHeight: measurement.scrollHeight,
        overflowY: measurement.overflowY,
        textExitsBoxY: measurement.textExitsBoxY
      }
    );
  };

  for (const key of [...criticalKeys].sort()) {
    checkCriticalMeasurement(key, raw.elements?.[key]);
  }

  for (const [label, expectedValue] of Object.entries(expected.opportunityValues || {})) {
    const measurement = raw.opportunityValues?.[label] || { present: false };
    const actual = String(measurement.text || "").trim();
    add(
      `opportunity-value:${label}`,
      "FAIL",
      !measurement.present || actual !== String(expectedValue),
      !measurement.present
        ? `missing Opportunity value: ${label}`
        : actual !== String(expectedValue)
          ? `Opportunity ${label} expected ${expectedValue}, got ${actual}`
          : `Opportunity ${label} equals ${expectedValue}`,
      { expected: String(expectedValue), actual }
    );
    checkCriticalMeasurement(`opportunity:${label}`, measurement);
  }

  const textFor = (entry) => entry.key
    ? String(raw.text?.byKey?.[entry.key] || "")
    : String(raw.text?.body || "");
  for (const [index, entryValue] of (expected.requiredText || []).entries()) {
    const entry = typeof entryValue === "string"
      ? { includes: [entryValue] }
      : entryValue;
    const haystack = textFor(entry);
    for (const needle of entry.includes || []) {
      const found = haystack.includes(needle);
      add(
        `required-text:${index}:${needle}`,
        "FAIL",
        !found,
        found
          ? `required text visible: ${needle}`
          : `required text missing${entry.key ? ` in ${entry.key}` : ""}: ${needle}`
      );
    }
  }

  for (const [index, entryValue] of (expected.forbiddenText || []).entries()) {
    const entry = typeof entryValue === "string"
      ? { includes: [entryValue] }
      : entryValue;
    const haystack = textFor(entry);
    for (const needle of entry.includes || []) {
      const found = haystack.includes(needle);
      add(
        `forbidden-text:${index}:${needle}`,
        "FAIL",
        found,
        found
          ? `forbidden text visible${entry.key ? ` in ${entry.key}` : ""}: ${needle}`
          : `forbidden text absent: ${needle}`
      );
    }
  }

  const expectedOrder = expected.order || defaults.order || [];
  const observedOrder = raw.dom?.surfaceOrder || [];
  const observedPositions = new Map(observedOrder.map((key, index) => [key, index]));
  const comparableOrder = expectedOrder.filter((key) => observedPositions.has(key));
  let wrongPair = null;
  for (let index = 1; index < comparableOrder.length; index += 1) {
    if (observedPositions.get(comparableOrder[index - 1]) >=
        observedPositions.get(comparableOrder[index])) {
      wrongPair = [comparableOrder[index - 1], comparableOrder[index]];
      break;
    }
  }
  add(
    "top-level-authority-order",
    "FAIL",
    Boolean(wrongPair),
    wrongPair
      ? `wrong DOM authority order: ${wrongPair[0]} must precede ${wrongPair[1]}`
      : "DOM authority order matches the fixture contract",
    { expected: comparableOrder, actual: observedOrder }
  );

  for (const key of expected.warnOnWrap || []) {
    const measurement = raw.elements?.[key];
    if (measurement?.present && measurement.wraps) {
      add(
        `readable-wrap:${key}`,
        "WARNING",
        true,
        `synthetic stress content wraps unusually but remains readable: ${key}`,
        { lineBoxCount: measurement.textRect?.lineBoxCount || null }
      );
    }
  }

  if (expected.contextWarningViewportMultiplier) {
    const limit = raw.viewport.height * expected.contextWarningViewportMultiplier;
    const contextY = raw.geometry?.contextY;
    if (Number.isFinite(contextY) && contextY > limit) {
      add(
        "deep-context-position",
        "WARNING",
        true,
        `Context begins at ${contextY}px under this intentional conditional state`,
        { contextY, warningThreshold: limit }
      );
    }
  }

  add(
    "geometry-summary",
    "INFORMATIONAL",
    false,
    "geometry and fold evidence recorded",
    {
      firstZoneHeight: raw.geometry?.firstZoneHeight ?? null,
      candidateY: raw.geometry?.candidateY ?? null,
      contextY: raw.geometry?.contextY ?? null,
      gexExposedSpace: raw.geometry?.gexExposedSpace ?? null,
      opportunityCandidateAdjacent:
        raw.geometry?.opportunityCandidateAdjacent ?? null,
      candidateBeforeContext: raw.geometry?.candidateBeforeContext ?? null,
      surfacesIntersectingFold: raw.fold?.intersecting || [],
      surfacesFullyAboveFold: raw.fold?.fullyAbove || []
    }
  );

  for (const note of expected.information || []) {
    add(`information:${checks.length}`, "INFORMATIONAL", false, note);
  }

  const failures = checks.filter((entry) =>
    entry.severity === "FAIL" && entry.status === "FAIL"
  );
  const warnings = checks.filter((entry) =>
    entry.severity === "WARNING" && entry.status === "FAIL"
  );
  const information = checks.filter((entry) =>
    entry.severity === "INFORMATIONAL"
  );
  const verdict = failures.length ? "FAIL" : warnings.length ? "WARNING" : "PASS";

  return {
    verdict,
    checks,
    failures: messageList(failures),
    warnings: messageList(warnings),
    information: messageList(information)
  };
}
