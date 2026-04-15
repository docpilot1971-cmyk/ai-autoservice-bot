"use strict";

/* =========================
   Mobile Navigation Toggle
========================= */
// TODO: Add menu toggle logic for mobile navigation.

/* FAQ Accordion */
(function () {
  const faqRoot = document.querySelector("[data-faq]");
  if (!faqRoot) return;

  const buttons = faqRoot.querySelectorAll(".faq__question");

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const isExpanded = button.getAttribute("aria-expanded") === "true";
      const panelId = button.getAttribute("aria-controls");
      const panel = panelId ? document.getElementById(panelId) : null;
      if (!panel) return;

      button.setAttribute("aria-expanded", String(!isExpanded));

      if (isExpanded) {
        panel.style.maxHeight = "0px";
      } else {
        panel.style.maxHeight = panel.scrollHeight + "px";
      }
    });
  });
})();


/* =========================
   Smooth Scroll Enhancements
========================= */
// TODO: Add optional smooth-scroll offset for sticky header.

/* =========================
   Lead Form Handling
========================= */
// TODO: Add form validation and submit handler (API / email service).

/* =========================
   Analytics Events
========================= */
// TODO: Track CTA clicks and form submissions for MVP demand testing.
/* Header Mobile Menu Toggle */
(function () {
  const burger = document.querySelector(".header__burger");
  const nav = document.getElementById("header-nav");
  const navLinks = document.querySelectorAll(".header__link");

  if (!burger || !nav) return;

  burger.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("is-open");
    burger.setAttribute("aria-expanded", String(isOpen));
  });

  navLinks.forEach((link) => {
    link.addEventListener("click", () => {
      nav.classList.remove("is-open");
      burger.setAttribute("aria-expanded", "false");
    });
  });
})();

/* =========================
   Contact Form Mailto Submit
========================= */
(function () {
  const form = document.getElementById("contact-form");
  if (!form) return;

  form.addEventListener("submit", (event) => {
    event.preventDefault();

    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    const name = (form.querySelector("#cf-name")?.value || "").trim();
    const phone = (form.querySelector("#cf-phone")?.value || "").trim();
    const message = (form.querySelector("#cf-message")?.value || "").trim();

    const to = "info@avtoritet34.ru";
    const subject = "Новая заявка с сайта";
    const body = [
      "Заявка с сайта инженерного сервисного центра",
      "",
      `Имя: ${name}`,
      `Телефон: ${phone}`,
      `Проблема: ${message}`
    ].join("\n");

    const mailtoUrl = `mailto:${to}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.location.href = mailtoUrl;
  });
})();

/* =========================
   Reviews Expand Toggle
========================= */
(function () {
  const toggles = document.querySelectorAll(".reviews__more");
  if (!toggles.length) return;

  toggles.forEach((toggle) => {
    toggle.addEventListener("click", (event) => {
      event.preventDefault();
      const card = toggle.closest(".reviews__card");
      if (!card) return;

      const isExpanded = card.classList.toggle("is-expanded");
      toggle.setAttribute("aria-expanded", String(isExpanded));
      toggle.textContent = isExpanded ? "свернуть" : "читать далее";
    });
  });
})();

/* =========================
   Gallery Lightbox
========================= */
(function () {
  const items = document.querySelectorAll(".gallery__item");
  if (!items.length) return;

  const overlay = document.createElement("div");
  overlay.className = "lightbox";
  overlay.setAttribute("aria-hidden", "true");
  overlay.innerHTML = `
    <div class="lightbox__backdrop" data-lightbox-close></div>
    <div class="lightbox__content" role="dialog" aria-modal="true" aria-label="Полноэкранный просмотр фото">
      <button class="lightbox__close" type="button" aria-label="Свернуть фото">
        <span class="lightbox__close-icon" aria-hidden="true">×</span>
      </button>
      <img class="lightbox__image" src="" alt="">
    </div>
  `;

  document.body.appendChild(overlay);

  const closeButton = overlay.querySelector(".lightbox__close");
  const imageElement = overlay.querySelector(".lightbox__image");
  let previousFocus = null;

  function openLightbox(sourceImage) {
    if (!imageElement) return;
    imageElement.src = sourceImage.currentSrc || sourceImage.src;
    imageElement.alt = sourceImage.alt || "Фото из галереи";
    overlay.classList.add("is-open");
    overlay.setAttribute("aria-hidden", "false");
    document.body.classList.add("is-lightbox-open");
    previousFocus = document.activeElement;
    closeButton?.focus();
  }

  function closeLightbox() {
    if (!imageElement) return;
    overlay.classList.remove("is-open");
    overlay.setAttribute("aria-hidden", "true");
    document.body.classList.remove("is-lightbox-open");
    imageElement.src = "";
    imageElement.alt = "";
    if (previousFocus instanceof HTMLElement) {
      previousFocus.focus();
    }
  }

  items.forEach((item) => {
    const image = item.querySelector(".gallery__image");
    if (!image) return;

    item.setAttribute("role", "button");
    item.setAttribute("tabindex", "0");
    item.setAttribute("aria-label", "Открыть фото в полноэкранном режиме");

    item.addEventListener("click", () => openLightbox(image));
    item.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      openLightbox(image);
    });
  });

  overlay.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    if (target.closest("[data-lightbox-close]") || target.closest(".lightbox__close")) {
      closeLightbox();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && overlay.classList.contains("is-open")) {
      closeLightbox();
    }
  });
})();

/* =========================
   Services Interactive Cards
========================= */
(function () {
  const servicesRoot = document.querySelector("[data-services-interactive]");
  if (!servicesRoot) return;

  const cards = Array.from(servicesRoot.querySelectorAll(".services__card"));
  if (!cards.length) return;

  function syncCardHeight(card) {
    const panel = card.querySelector(".services__panel");
    if (!panel) return;

    if (!card.classList.contains("is-open")) {
      panel.style.maxHeight = "0px";
      return;
    }

    panel.style.maxHeight = panel.scrollHeight + 80 + "px";
  }

  function closeCard(card) {
    const trigger = card.querySelector(".services__trigger");
    card.classList.remove("is-open");
    if (trigger) trigger.setAttribute("aria-expanded", "false");
    syncCardHeight(card);
  }

  function openCard(card) {
    const trigger = card.querySelector(".services__trigger");
    card.classList.add("is-open");
    if (trigger) trigger.setAttribute("aria-expanded", "true");
    syncCardHeight(card);
  }

  cards.forEach((card) => {
    const trigger = card.querySelector(".services__trigger");
    if (!trigger) return;

    trigger.addEventListener("click", () => {
      const isOpen = card.classList.contains("is-open");

      cards.forEach((otherCard) => {
        if (otherCard !== card) {
          closeCard(otherCard);
        }
      });

      if (isOpen) {
        closeCard(card);
      } else {
        openCard(card);
      }
    });

    trigger.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      trigger.click();
    });
  });

  const autoCard = document.getElementById("service-auto");
  if (autoCard) {
    const subButtons = Array.from(autoCard.querySelectorAll(".services__subbtn"));
    const subPanels = Array.from(autoCard.querySelectorAll(".services__subpanel"));

    function refreshAutoCardHeight() {
      requestAnimationFrame(() => {
        syncCardHeight(autoCard);
      });
      setTimeout(() => {
        syncCardHeight(autoCard);
      }, 120);
    }

    function activateSubpanel(targetId) {
      subButtons.forEach((button) => {
        const isActive = Boolean(targetId) && button.dataset.subtarget === targetId;
        button.classList.toggle("is-active", isActive);
        button.setAttribute("aria-pressed", isActive ? "true" : "false");
      });

      subPanels.forEach((panel) => {
        const isActive = Boolean(targetId) && panel.id === targetId;
        panel.classList.toggle("is-active", isActive);
        panel.style.maxHeight = isActive ? "none" : "0px";
      });

      refreshAutoCardHeight();
    }

    subButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const targetId = button.dataset.subtarget;
        if (!targetId) return;

        const isAlreadyActive = button.classList.contains("is-active");
        if (isAlreadyActive) {
          activateSubpanel("");
          return;
        }

        activateSubpanel(targetId);
      });
    });

    const initialSub = autoCard.querySelector(".services__subbtn.is-active")?.dataset.subtarget;
    if (initialSub) {
      activateSubpanel(initialSub);
    }
  }

  window.addEventListener("resize", () => {
    cards.forEach((card) => syncCardHeight(card));
  });
})();
