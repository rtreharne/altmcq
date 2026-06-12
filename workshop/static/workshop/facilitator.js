const sections = JSON.parse(document.getElementById("sections-data").textContent);
const scenarioNames = JSON.parse(document.getElementById("scenario-data").textContent);
const STORAGE_KEY = "altmcq.facilitator.timers.v1";

let currentStep = 0;
let remaining = sections[0].duration;
let timer = null;
let timerRunning = false;
let timerEndAt = null;
let masterTimer = null;
let masterRemaining = 45 * 60;
let masterStarted = false;
let masterEndAt = null;
let discussionAlerts = {};
let edithFadeTimer = null;
let edithFadeOutTimer = null;
let edithActiveKey = null;
let edithUnlocked = false;
let groupTimer = {
  groupIndex: 0,
  phase: "ready",
};

const label = document.getElementById("section-label");
const title = document.getElementById("section-title");
const subtitle = document.getElementById("section-subtitle");
const masterClockContainer = document.querySelector(".master-clock");
const masterStart = document.getElementById("master-start");
const masterReset = document.getElementById("master-reset");
const masterClock = document.getElementById("master-clock-display");
const masterTime = document.getElementById("master-time");
const startPause = document.getElementById("start-pause");
const soundTrigger = document.getElementById("sound-trigger");
const edithTrigger = document.getElementById("edith-trigger");
const woogahAudio = document.getElementById("woogah-audio");
const edithAudio = document.getElementById("edith-audio");
const stepButtons = Array.from(document.querySelectorAll(".step-button"));
const sectionBlocks = Array.from(document.querySelectorAll("[data-section-block]"));
const sectionTimers = Array.from(document.querySelectorAll("[data-section-timer]"));

function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, "0");
  const secs = (seconds % 60).toString().padStart(2, "0");
  return `${minutes}:${secs}`;
}

function secondsUntil(timestamp) {
  return Math.max(0, Math.ceil((timestamp - Date.now()) / 1000));
}

function saveState() {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      currentStep,
      sectionTimer: {
        remaining,
        running: timerRunning,
        endAt: timerEndAt,
        groupIndex: groupTimer.groupIndex,
        phase: groupTimer.phase,
      },
      masterTimer: {
        remaining: masterRemaining,
        started: masterStarted,
        endAt: masterEndAt,
      },
      discussionAlerts,
    }),
  );
}

function loadState() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY));
  } catch {
    return null;
  }
}

function stopTimer(status = "Paused", persist = true, stopAudio = true) {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
  if (stopAudio) {
    stopEdith();
  }
  timerRunning = false;
  timerEndAt = null;
  const block = currentGroupTimerBlock();
  if (block && status === "Done") {
    block.classList.remove("is-warning");
  }
  startPause.textContent = "Start";
  if (persist) {
    saveState();
  }
}

function renderTimer() {
  const section = sections[currentStep];
  sectionTimers.forEach((timerElement) => {
    const timerSection = sections.find((item) => item.key === timerElement.dataset.sectionTimer);
    const isCurrentTimer = timerElement.dataset.sectionTimer === section.key;
    timerElement.textContent = isCurrentTimer ? formatTime(remaining) : formatTime(timerSection.duration);
    timerElement.classList.toggle("is-warning", isCurrentTimer && remaining <= 60);
  });
  updateGroupTimerDisplay();
}

function playWoogah() {
  woogahAudio.pause();
  woogahAudio.currentTime = 0;
  woogahAudio.play().catch(() => {});
}

function maybePlayDiscussionWarning() {
  const section = sections[currentStep];
  if (section.mode !== "discussion" || remaining > 60 || remaining <= 0 || discussionAlerts[section.key]) {
    return;
  }

  discussionAlerts[section.key] = true;
  playWoogah();
  saveState();
}

function stopEdith() {
  if (edithFadeTimer) {
    clearInterval(edithFadeTimer);
    edithFadeTimer = null;
  }
  if (edithFadeOutTimer) {
    clearInterval(edithFadeOutTimer);
    edithFadeOutTimer = null;
  }
  edithActiveKey = null;
  edithAudio.pause();
  edithAudio.volume = 0;
}

function unlockEdithAudio() {
  if (edithUnlocked) {
    return;
  }

  edithAudio.muted = true;
  edithAudio.volume = 0;
  edithAudio.play()
    .then(() => {
      edithAudio.pause();
      edithAudio.currentTime = 0;
      edithAudio.muted = false;
      edithUnlocked = true;
    })
    .catch(() => {
      edithAudio.muted = false;
    });
}

function startEdithFadeIn() {
  const activeKey = `${sections[currentStep].key}:${groupTimer.groupIndex}`;
  if (edithActiveKey === activeKey) {
    return;
  }

  stopEdith();
  edithActiveKey = activeKey;
  edithAudio.volume = 0;
  edithAudio.currentTime = 0;
  edithAudio.play().catch(() => {});
  edithFadeTimer = setInterval(() => {
    const millisecondsLeft = timerEndAt ? Math.max(0, timerEndAt - Date.now()) : remaining * 1000;
    const progress = Math.min(1, Math.max(0, (10000 - millisecondsLeft) / 10000));
    edithAudio.volume = progress;
    if (progress >= 1) {
      clearInterval(edithFadeTimer);
      edithFadeTimer = null;
    }
  }, 100);
}

function playEdith() {
  stopEdith();
  edithAudio.volume = 1;
  edithAudio.currentTime = 0;
  edithAudio.play().catch(() => {});
}

function toggleEdith() {
  if (!edithAudio.paused) {
    stopEdith();
    return;
  }

  playEdith();
}

function startEdithFadeOut() {
  if (!edithActiveKey) {
    return;
  }

  if (edithFadeTimer) {
    clearInterval(edithFadeTimer);
    edithFadeTimer = null;
  }
  edithAudio.volume = 1;
  const startedAt = Date.now();
  edithFadeOutTimer = setInterval(() => {
    const progress = Math.min(1, (Date.now() - startedAt) / 2000);
    edithAudio.volume = Math.max(0, 1 - progress);
    if (progress >= 1) {
      stopEdith();
    }
  }, 50);
}

function updateEdithCue() {
  const section = sections[currentStep];
  if (section.mode === "group-timer" && groupTimer.phase === "active" && remaining <= 10 && remaining > 0) {
    startEdithFadeIn();
  }
}

function renderMasterClock() {
  masterTime.textContent = formatTime(masterRemaining);
  masterClock.classList.toggle("is-warning", masterRemaining <= 5 * 60);
}

function updateMasterClockVisibility() {
  masterClockContainer.classList.toggle("is-hidden", sections[currentStep].mode === "group-timer");
}

function startMasterClock() {
  masterStarted = true;
  masterStart.classList.add("is-hidden");
  masterClock.classList.remove("is-hidden");
  masterEndAt = Date.now() + masterRemaining * 1000;
  renderMasterClock();
  saveState();

  if (masterTimer) {
    return;
  }

  masterTimer = setInterval(() => {
    masterRemaining = secondsUntil(masterEndAt);
    renderMasterClock();
    saveState();
    if (masterRemaining === 0) {
      clearInterval(masterTimer);
      masterTimer = null;
      masterEndAt = null;
      saveState();
    }
  }, 1000);
}

function restoreMasterClock(savedMasterTimer) {
  if (!savedMasterTimer || !savedMasterTimer.started) {
    renderMasterClock();
    return;
  }

  masterStarted = true;
  masterEndAt = savedMasterTimer.endAt || null;
  masterRemaining = masterEndAt ? secondsUntil(masterEndAt) : savedMasterTimer.remaining;
  masterStart.classList.add("is-hidden");
  masterClock.classList.remove("is-hidden");
  renderMasterClock();

  if (masterEndAt && masterRemaining > 0) {
    masterTimer = setInterval(() => {
      masterRemaining = secondsUntil(masterEndAt);
      renderMasterClock();
      saveState();
      if (masterRemaining === 0) {
        clearInterval(masterTimer);
        masterTimer = null;
        masterEndAt = null;
        saveState();
      }
    }, 1000);
  }
}

function resetMasterClock() {
  if (masterTimer) {
    clearInterval(masterTimer);
    masterTimer = null;
  }
  masterRemaining = 45 * 60;
  masterStarted = false;
  masterEndAt = null;
  masterClock.classList.add("is-hidden");
  masterClock.classList.remove("is-warning");
  masterStart.classList.remove("is-hidden");
  renderMasterClock();
  saveState();
}

function currentGroupTimerBlock() {
  return document.querySelector(".group-timer:not(.is-hidden)");
}

function updateGroupTimerDisplay() {
  const block = currentGroupTimerBlock();
  if (!block) {
    return;
  }

  const section = sections[currentStep];
  const groupName = scenarioNames[groupTimer.groupIndex] || "Scenario group";
  const isActive = groupTimer.phase === "active";
  const isReady = groupTimer.phase === "ready";
  const isLastGroup = groupTimer.groupIndex === scenarioNames.length - 1;
  block.classList.toggle("is-warning", isActive && remaining <= 10);
  block.classList.toggle("is-ready", isReady);
  block.querySelector(".group-phase").textContent = isActive ? section.action : `Get ready: ${groupName}`;
  block.querySelector(".group-name").textContent = groupName;
  block.querySelector(".group-countdown").textContent = formatTime(remaining);
  block.querySelector(".group-action").textContent = `Group ${groupTimer.groupIndex + 1} of ${scenarioNames.length}`;
  block.querySelector(".group-next").textContent = isActive && isLastGroup ? "Finish" : "Next";
}

function resetGroupTimer(section) {
  groupTimer = {
    groupIndex: 0,
    phase: section.mode === "group-timer" ? "ready" : "standard",
  };
}

function hasAutoTimer(section) {
  return section && (section.mode === "discussion" || section.mode === "pass" || section.mode === "group-timer");
}

function advanceGroupTimerPhase() {
  const section = sections[currentStep];
  if (groupTimer.phase === "ready") {
    groupTimer.phase = "active";
    remaining = 60;
    timerEndAt = Date.now() + remaining * 1000;
    renderTimer();
    saveState();
    return;
  }

  if (groupTimer.groupIndex < scenarioNames.length - 1) {
    startEdithFadeOut();
    groupTimer.groupIndex += 1;
    groupTimer.phase = "ready";
    remaining = 5;
    timerEndAt = Date.now() + remaining * 1000;
    renderTimer();
    saveState();
    return;
  }

  startEdithFadeOut();
  advanceToNextSubsection(true, true);
}

function advanceToNextSubsection(autoStart = true, preserveEdith = false) {
  setStep(currentStep + 1, {autoStartTimer: autoStart, preserveEdith});
}

function setStep(index, options = {}) {
  const shouldResetTimer = options.resetTimer !== false;
  const shouldPersist = options.persist !== false;
  const shouldAutoStartTimer = options.autoStartTimer !== false;
  const preserveEdith = options.preserveEdith === true;
  currentStep = Math.max(0, Math.min(index, sections.length - 1));
  const section = sections[currentStep];
  if (shouldResetTimer) {
    stopTimer("Ready", false, !preserveEdith);
    remaining = section.duration;
    resetGroupTimer(section);
    if (section.mode === "discussion") {
      delete discussionAlerts[section.key];
    }
  }
  label.textContent = section.label;
  title.textContent = section.title;
  subtitle.textContent = section.subtitle;

  stepButtons.forEach((button, buttonIndex) => {
    button.classList.toggle("is-active", buttonIndex === currentStep);
  });

  sectionBlocks.forEach((block) => {
    block.classList.toggle("is-hidden", block.dataset.sectionBlock !== section.key);
  });

  if (section.key === "results") {
    fetchResults();
  }

  updateMasterClockVisibility();
  renderTimer();
  if (shouldPersist) {
    saveState();
  }
  if (shouldResetTimer && shouldAutoStartTimer && hasAutoTimer(section)) {
    startTimer();
  }
}

function startTimer() {
  unlockEdithAudio();
  if (timer) {
    stopTimer();
    return;
  }
  startPause.textContent = "Pause";
  timerRunning = true;
  timerEndAt = Date.now() + remaining * 1000;
  saveState();
  timer = setInterval(() => {
    remaining = secondsUntil(timerEndAt);
    renderTimer();
    maybePlayDiscussionWarning();
    updateEdithCue();
    if (remaining === 0) {
      if (sections[currentStep].mode === "group-timer") {
        advanceGroupTimerPhase();
      } else if (sections[currentStep].mode === "discussion" || sections[currentStep].mode === "pass") {
        advanceToNextSubsection(true);
      } else {
        stopTimer("Time");
      }
    } else {
      saveState();
    }
  }, 1000);
}

function restoreSectionTimer(savedSectionTimer) {
  if (!savedSectionTimer) {
    return;
  }

  groupTimer = {
    groupIndex: savedSectionTimer.groupIndex || 0,
    phase: savedSectionTimer.phase || groupTimer.phase,
  };
  remaining = savedSectionTimer.running && savedSectionTimer.endAt
    ? secondsUntil(savedSectionTimer.endAt)
    : savedSectionTimer.remaining;
  timerEndAt = savedSectionTimer.running && savedSectionTimer.endAt ? savedSectionTimer.endAt : null;
  renderTimer();

  if (
    savedSectionTimer.running
    && remaining === 0
    && (sections[currentStep].mode === "discussion" || sections[currentStep].mode === "pass")
  ) {
    advanceToNextSubsection(true);
    return;
  }

  if (savedSectionTimer.running && remaining > 0) {
    timerRunning = true;
    startPause.textContent = "Pause";
    timer = setInterval(() => {
      remaining = secondsUntil(timerEndAt);
      renderTimer();
      maybePlayDiscussionWarning();
      updateEdithCue();
      if (remaining === 0) {
        if (sections[currentStep].mode === "group-timer") {
          advanceGroupTimerPhase();
        } else if (sections[currentStep].mode === "discussion" || sections[currentStep].mode === "pass") {
          advanceToNextSubsection(true);
        } else {
          stopTimer("Time");
        }
      } else {
        saveState();
      }
    }, 1000);
  }
}

function fetchResults() {
  fetch("/results.json", {headers: {"Accept": "application/json"}})
    .then((response) => response.json())
    .then((data) => {
      document.getElementById("total-votes").textContent = data.total;
      const resultsList = document.getElementById("results-list");
      resultsList.innerHTML = data.scenarios.map((scenario) => `
        <div class="result-row">
          <div>
            <strong>${scenario.title}</strong>
            <span>${scenario.votes} votes - ${scenario.percent}%</span>
          </div>
          <div class="bar"><span style="width: ${scenario.percent}%"></span></div>
        </div>
      `).join("");

    });
}

document.getElementById("prev-section").addEventListener("click", () => setStep(currentStep - 1));
document.getElementById("next-section").addEventListener("click", () => setStep(currentStep + 1));
document.getElementById("reset-timer").addEventListener("click", () => setStep(currentStep));
masterStart.addEventListener("click", () => {
  unlockEdithAudio();
  startMasterClock();
});
masterReset.addEventListener("click", resetMasterClock);
startPause.addEventListener("click", startTimer);
soundTrigger.addEventListener("click", playWoogah);
edithTrigger.addEventListener("click", toggleEdith);

stepButtons.forEach((button) => {
  button.addEventListener("click", () => {
    unlockEdithAudio();
    setStep(Number(button.dataset.step));
  });
});

document.querySelectorAll(".group-next").forEach((button) => {
  button.addEventListener("click", () => {
    unlockEdithAudio();
    advanceGroupTimerPhase();
  });
});

window.addEventListener("beforeunload", saveState);

setInterval(() => {
  if (sections[currentStep].key === "results") {
    fetchResults();
  }
}, 5000);

const savedState = loadState();
if (savedState && Number.isInteger(savedState.currentStep)) {
  discussionAlerts = savedState.discussionAlerts || {};
  currentStep = Math.max(0, Math.min(savedState.currentStep, sections.length - 1));
  setStep(currentStep, {resetTimer: false, persist: false, autoStartTimer: false});
  restoreSectionTimer(savedState.sectionTimer);
  restoreMasterClock(savedState.masterTimer);
  saveState();
} else {
  setStep(0, {autoStartTimer: false});
  renderMasterClock();
}
