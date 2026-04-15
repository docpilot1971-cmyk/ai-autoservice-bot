"use strict";

(function () {
  const navButtons = Array.from(document.querySelectorAll(".services-nav__btn"));
  const accordions = Array.from(document.querySelectorAll(".service-accordion"));
  const autoSection = document.getElementById("auto");

  if (!navButtons.length || !accordions.length) return;

  function getContent(accordion) {
    const trigger = accordion.querySelector(".service-accordion__header");
    if (!trigger) return null;
    const panelId = trigger.getAttribute("aria-controls");
    return panelId ? document.getElementById(panelId) : null;
  }

  function setActiveButton(targetId) {
    navButtons.forEach((button) => {
      const isActive = button.dataset.target === targetId;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-current", isActive ? "true" : "false");
    });
  }

  function closeAccordion(accordion) {
    const trigger = accordion.querySelector(".service-accordion__header");
    const content = getContent(accordion);
    accordion.classList.remove("service-accordion--open");
    if (trigger) trigger.setAttribute("aria-expanded", "false");
    if (content) content.style.maxHeight = "0px";
  }

  function syncOpenHeights() {
    accordions.forEach((accordion) => {
      if (!accordion.classList.contains("service-accordion--open")) return;
      const content = getContent(accordion);
      if (content) content.style.maxHeight = content.scrollHeight + "px";
    });
  }

  function scrollAccordionIntoView(accordion) {
    requestAnimationFrame(() => {
      accordion.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  }

  function openAccordion(targetId, shouldScroll, canToggleClose) {
    const targetAccordion = document.getElementById(targetId);
    if (!targetAccordion) return;
    const targetIsOpen = targetAccordion.classList.contains("service-accordion--open");

    if (canToggleClose && targetIsOpen) {
      closeAccordion(targetAccordion);
      setActiveButton("");
      return;
    }

    accordions.forEach((accordion) => {
      const trigger = accordion.querySelector(".service-accordion__header");
      const content = getContent(accordion);
      const isOpen = accordion === targetAccordion;

      accordion.classList.toggle("service-accordion--open", isOpen);
      if (trigger) trigger.setAttribute("aria-expanded", String(isOpen));
      if (content) content.style.maxHeight = isOpen ? content.scrollHeight + "px" : "0px";
    });

    setActiveButton(targetId);

    if (shouldScroll) {
      scrollAccordionIntoView(targetAccordion);
    }
  }

  navButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const targetId = button.dataset.target;
      if (!targetId) return;
      if (window.location.hash !== "#" + targetId) {
        history.replaceState(null, "", "#" + targetId);
      }
      openAccordion(targetId, true, false);
    });
  });

  accordions.forEach((accordion) => {
    const trigger = accordion.querySelector(".service-accordion__header");
    if (!trigger) return;

    trigger.addEventListener("click", () => {
      const targetId = accordion.id;
      if (!targetId) return;
      if (window.location.hash !== "#" + targetId) {
        history.replaceState(null, "", "#" + targetId);
      }
      openAccordion(targetId, false, true);
    });
  });

  if (autoSection) {
    const subButtons = Array.from(autoSection.querySelectorAll(".service-subnav__btn"));
    const subPanels = Array.from(autoSection.querySelectorAll(".service-subpanel"));
    const autoMoreLink = document.getElementById("auto-more-link");
    const autoMoreMap = {
      "auto-engine": {
        href: "remont-dvigatelya.html",
        aria: "Перейти на страницу ремонта двигателя"
      },
      "auto-gearbox": {
        href: "remont-kpp.html",
        aria: "Перейти на страницу ремонта коробки передач"
      },
      "auto-suspension": {
        href: "remont-hodovoy.html",
        aria: "Перейти на страницу ремонта ходовой части"
      },
      "auto-electrics": {
        href: "avtoelektrika.html",
        aria: "Перейти на страницу ремонта автоэлектрики"
      }
    };

    function syncAutoMoreLink(targetId) {
      if (!autoMoreLink) return;
      const config = targetId ? autoMoreMap[targetId] : null;
      if (!config) {
        autoMoreLink.hidden = true;
        return;
      }
      autoMoreLink.hidden = false;
      autoMoreLink.setAttribute("href", config.href);
      autoMoreLink.setAttribute("aria-label", config.aria);
    }

    function openSubpanel(targetId) {
      subButtons.forEach((button) => {
        const isActive = Boolean(targetId) && button.dataset.subtarget === targetId;
        button.classList.toggle("is-active", isActive);
        button.setAttribute("aria-pressed", isActive ? "true" : "false");
      });

      subPanels.forEach((panel) => {
        const isActive = Boolean(targetId) && panel.id === targetId;
        panel.classList.toggle("is-active", isActive);
      });

      syncAutoMoreLink(targetId);
      requestAnimationFrame(syncOpenHeights);
    }

    subButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const targetId = button.dataset.subtarget;
        if (!targetId) return;
        if (button.classList.contains("is-active")) {
          openSubpanel("");
          return;
        }
        openSubpanel(targetId);
      });
    });

    const initialSub = autoSection.querySelector(".service-subnav__btn.is-active")?.dataset.subtarget;
    if (initialSub) {
      openSubpanel(initialSub);
    } else {
      syncAutoMoreLink("");
    }
  }

  window.addEventListener("hashchange", () => {
    const targetId = window.location.hash.replace("#", "").trim();
    if (!targetId || !document.getElementById(targetId)) return;
    openAccordion(targetId, true, false);
  });

  window.addEventListener("resize", syncOpenHeights);
  window.addEventListener("load", syncOpenHeights);

  const initialTarget = window.location.hash.replace("#", "").trim();
  if (initialTarget && document.getElementById(initialTarget)) {
    openAccordion(initialTarget, true, false);
  } else {
    openAccordion("auto", false, false);
  }
})();
