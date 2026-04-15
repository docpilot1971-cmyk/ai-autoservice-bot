"use strict";

(function () {
  const galleries = document.querySelectorAll(".engine-gallery");
  const galleryItems = document.querySelectorAll(".engine-gallery__item");
  const lightbox = document.getElementById("engine-lightbox");

  function stripLeadingOrder(value) {
    if (!value) return "";
    return value.replace(/^\s*\d+(?:\.\d+)*\.?\s*/, "").trim();
  }

  galleries.forEach((gallery) => {
    const items = Array.from(gallery.querySelectorAll(".engine-gallery__item"));
    gallery.classList.remove("is-expanded");
    if (items.length <= 3) return;

    const collapsedItems = items.slice(3);
    collapsedItems.forEach((item) => {
      item.classList.add("is-collapsed", "is-hidden");
      item.setAttribute("aria-hidden", "true");
    });

    let controls = gallery.nextElementSibling;
    if (!controls || !controls.classList.contains("engine-gallery__more")) {
      controls = document.createElement("div");
      controls.className = "engine-gallery__more";
      gallery.insertAdjacentElement("afterend", controls);
    }

    let toggleButton = controls.querySelector(".engine-gallery__toggle");
    if (!toggleButton) {
      toggleButton = document.createElement("button");
      toggleButton.type = "button";
      toggleButton.className = "engine-gallery__toggle";
      toggleButton.setAttribute("aria-expanded", "false");
      toggleButton.dataset.collapsedText = "смотреть далее";
      toggleButton.dataset.expandedText = "свернуть";
      toggleButton.innerHTML =
        '<span class="engine-gallery__toggle-arrow" aria-hidden="true">→</span><span class="engine-gallery__toggle-text">смотреть далее</span>';
      controls.appendChild(toggleButton);
    }

    const toggleLabel = toggleButton.querySelector(".engine-gallery__toggle-text");
    const expandedText = toggleButton.dataset.expandedText || "свернуть";
    const collapsedText = toggleButton.dataset.collapsedText || "смотреть далее";
    let isExpanded = false;

    function updateToggleState() {
      gallery.classList.toggle("is-expanded", isExpanded);
      collapsedItems.forEach((item) => {
        item.classList.toggle("is-hidden", !isExpanded);
        item.setAttribute("aria-hidden", String(!isExpanded));
      });

      toggleButton.classList.toggle("is-open", isExpanded);
      toggleButton.setAttribute("aria-expanded", String(isExpanded));
      if (toggleLabel) toggleLabel.textContent = isExpanded ? expandedText : collapsedText;
    }

    updateToggleState();
    toggleButton.addEventListener("click", () => {
      isExpanded = !isExpanded;
      updateToggleState();
    });
  });

  if (!galleryItems.length || !lightbox) return;

  const backdrop = lightbox.querySelector(".engine-lightbox__backdrop");
  const closeBtn = lightbox.querySelector(".engine-lightbox__close");
  const image = lightbox.querySelector(".engine-lightbox__image");
  const caption = lightbox.querySelector(".engine-lightbox__caption");
  let lastFocused = null;

  function openLightbox(source, text) {
    if (!image || !caption) return;
    image.src = source.currentSrc || source.src;
    image.alt = source.alt || "Фото ремонта двигателя";
    caption.textContent = text || "";
    lightbox.classList.add("is-open");
    lightbox.setAttribute("aria-hidden", "false");
    document.body.classList.add("is-lightbox-open");
    lastFocused = document.activeElement;
    closeBtn?.focus();
  }

  function closeLightbox() {
    if (!image || !caption) return;
    lightbox.classList.remove("is-open");
    lightbox.setAttribute("aria-hidden", "true");
    image.src = "";
    image.alt = "";
    caption.textContent = "";
    document.body.classList.remove("is-lightbox-open");
    if (lastFocused instanceof HTMLElement) lastFocused.focus();
  }

  galleryItems.forEach((item) => {
    const img = item.querySelector(".engine-gallery__image");
    const figcaption = item.querySelector(".engine-gallery__caption");
    if (!img) return;

    if (figcaption) {
      figcaption.textContent = stripLeadingOrder(figcaption.textContent || "");
    }
    img.alt = stripLeadingOrder(img.alt || "");

    item.setAttribute("tabindex", "0");
    item.setAttribute("role", "button");
    item.setAttribute("aria-label", "Открыть изображение в полном размере");

    item.addEventListener("click", () => openLightbox(img, figcaption?.textContent?.trim() || ""));
    item.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      openLightbox(img, figcaption?.textContent?.trim() || "");
    });
  });

  backdrop?.addEventListener("click", closeLightbox);
  closeBtn?.addEventListener("click", closeLightbox);

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && lightbox.classList.contains("is-open")) {
      closeLightbox();
    }
  });
})();
