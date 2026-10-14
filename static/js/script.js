/* PASASA prototype interactions (vanilla JS only). */
document.addEventListener("DOMContentLoaded", () => {
    initModeToggle();
    initLanguageSwitch();
    initMapDetailPage();
});

function initModeToggle() {
    const modeSwitch = document.querySelector("[data-mode-switch]");
    if (!modeSwitch) return;

    const modeButtons = Array.from(modeSwitch.querySelectorAll(".mode-btn"));
    modeButtons.forEach((btn) => {
        btn.addEventListener("click", (event) => {
            const href = btn.getAttribute("href");
            if (href) event.preventDefault();
            setActiveMode(modeButtons, btn.dataset.mode);
            btn.classList.add("is-switching");
            if (href) {
                setTimeout(() => {
                    window.location.href = href;
                }, 170);
            }
        });
    });
}

function setActiveMode(buttons, mode) {
    buttons.forEach((btn) => {
        btn.classList.toggle("is-active", btn.dataset.mode === mode);
        btn.classList.remove("is-switching");
    });
}

function initLanguageSwitch() {
    const langForm = document.querySelector(".lang-switch");
    if (!langForm) return;

    const langButtons = Array.from(langForm.querySelectorAll(".lang-btn"));
    langButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            btn.classList.add("is-switching");
        });
    });
}

function initMapDetailPage() {
    const page = document.querySelector(".map-detail-page");
    if (!page) return;

    const pins = Array.from(document.querySelectorAll(".pin"));
    const firstPin = pins[0] || null;
    const state = {
        zoom: 0.8,
        minZoom: 0.7,
        maxZoom: 5.3,
        panX: 0,
        panY: 0,
        isDragging: false,
        dragStartX: 0,
        dragStartY: 0,
        userFilterRating: 0,
        adminFilterRating: 0,
        myRating: 0,
        selectedPinId: firstPin ? firstPin.dataset.pinId : null,
        spotData: getSpotDataFromPage(),
        mediaItems: [],
        mediaIndex: 0,
    };

    initTabs();
    initZoom(state);
    initStars(state);
    initPins(state);
    initSpotActions(state);
    initMediaSlider(state);
    initMediaLightbox(state);
    paintPinsByRating();
    initCustomDropdowns();
    initFilters(state);
    initMapCursorCoords(state);

    if (state.selectedPinId) {
        renderSpot(state.selectedPinId, state);
    } else {
        renderEmptySpotState();
    }
}

function initTabs() {
    const tabButtons = Array.from(document.querySelectorAll(".tab-btn"));
    const tabPanels = Array.from(document.querySelectorAll("[data-tab-panel]"));

    tabButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const target = btn.dataset.tabTarget;
            tabButtons.forEach((b) => b.classList.toggle("is-active", b === btn));
            tabPanels.forEach((panel) => {
                panel.classList.toggle("is-active", panel.dataset.tabPanel === target);
            });
        });
    });
}

function initZoom(state) {
    const frame = document.querySelector(".map-frame");
    const canvas = document.querySelector("[data-map-canvas]");
    const zoomButtons = Array.from(document.querySelectorAll("[data-zoom-action]"));
    if (!frame || !canvas || zoomButtons.length === 0) return;

    centerMapInFrame(state, frame);
    applyMapTransform(canvas, state);

    zoomButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const action = btn.dataset.zoomAction;
            const nextZoom = clamp(
                state.zoom + (action === "in" ? 0.12 : -0.06),
                state.minZoom,
                state.maxZoom
            );
            const rect = frame.getBoundingClientRect();
            zoomAtPoint(state, canvas, rect.width / 2, rect.height / 2, nextZoom);
        });
    });

    frame.addEventListener(
        "wheel",
        (event) => {
            event.preventDefault();
            const rect = frame.getBoundingClientRect();
            const pointX = event.clientX - rect.left;
            const pointY = event.clientY - rect.top;
            const zoomFactor = event.deltaY < 0 ? 1.1 : 0.95;
            const nextZoom = clamp(state.zoom * zoomFactor, state.minZoom, state.maxZoom);
            zoomAtPoint(state, canvas, pointX, pointY, nextZoom);
        },
        { passive: false }
    );

    frame.addEventListener("mousedown", (event) => {
        if (event.button !== 0) return;
        if (event.target.closest(".pin")) return;
        state.isDragging = true;
        state.dragStartX = event.clientX - state.panX;
        state.dragStartY = event.clientY - state.panY;
        frame.classList.add("is-dragging");
    });

    window.addEventListener("mousemove", (event) => {
        if (!state.isDragging) return;
        state.panX = event.clientX - state.dragStartX;
        state.panY = event.clientY - state.dragStartY;
        applyMapTransform(canvas, state);
    });

    window.addEventListener("mouseup", () => {
        if (!state.isDragging) return;
        state.isDragging = false;
        frame.classList.remove("is-dragging");
    });

    window.addEventListener("resize", () => {
        if (state.isDragging) return;
        centerMapInFrame(state, frame);
        applyMapTransform(canvas, state);
    });
}

function initStars(state) {
    initFilterStarGroup({
        rowSelector: "[data-user-filter-stars]",
        resetSelector: "[data-user-rating-reset]",
        getValue: () => state.userFilterRating,
        setValue: (value) => {
            state.userFilterRating = value;
            applyFilters(state);
        },
    });

    initFilterStarGroup({
        rowSelector: "[data-admin-rating-stars]",
        resetSelector: "[data-admin-rating-reset]",
        getValue: () => state.adminFilterRating,
        setValue: (value) => {
            state.adminFilterRating = value;
            applyFilters(state);
        },
    });
}

function initFilterStarGroup(config) {
    const starRow = document.querySelector(config.rowSelector);
    if (!starRow) return;
    const stars = Array.from(starRow.querySelectorAll(".star"));
    if (stars.length === 0) return;
    const resetButton = document.querySelector(config.resetSelector);

    stars.forEach((star) => {
        star.addEventListener("click", () => {
            const rating = Number(star.dataset.starValue);
            config.setValue(rating);
            paintStars(stars, config.getValue(), false);
        });

        star.addEventListener("mouseenter", () => {
            paintStars(stars, Number(star.dataset.starValue), true);
        });
    });

    starRow.addEventListener("mouseleave", () => {
        paintStars(stars, config.getValue(), false);
    });

    if (resetButton) {
        resetButton.addEventListener("click", () => {
            config.setValue(0);
            paintStars(stars, 0, false);
        });
    }
}

function paintStars(stars, rating, isPreview) {
    const colorMap = {
        1: "#2ebc62",
        2: "#3b7fdc",
        3: "#8751d6",
        4: "#d6c245",
        5: "#36c7db",
    };

    const selectedColor = colorMap[rating] || "#c3cdda";
    stars.forEach((star) => {
        const value = Number(star.dataset.starValue);
        const isActive = value <= rating;
        star.classList.toggle("is-active", isActive);
        star.classList.toggle("is-preview", isActive && Boolean(isPreview));
        star.style.color = isActive ? selectedColor : "#c3cdda";
    });
}

function paintPinsByRating() {
    const pins = Array.from(document.querySelectorAll(".pin"));
    pins.forEach((pin) => {
        const rating = Number(pin.dataset.adminRating);
        [1, 2, 3, 4, 5].forEach((value) => {
            pin.classList.toggle(`pin--rating-${value}`, rating === value);
        });
        pin.style.setProperty("--pin-color", getRatingColor(rating));
    });
}

function initPins(state) {
    const pins = Array.from(document.querySelectorAll(".pin"));
    pins.forEach((pin) => {
        pin.addEventListener("click", () => {
            state.selectedPinId = pin.dataset.pinId;
            pins.forEach((p) => p.classList.toggle("is-selected", p === pin));
            renderSpot(state.selectedPinId, state);
        });
    });

    const defaultPin = pins.find((p) => p.dataset.pinId === state.selectedPinId);
    if (defaultPin) defaultPin.classList.add("is-selected");
}

function initFilters(state) {
    const selects = Array.from(document.querySelectorAll("select[data-filter]"));
    const featureChecks = Array.from(document.querySelectorAll("input[type='checkbox'][data-feature]"));

    const apply = () => applyFilters(state);
    selects.forEach((select) => select.addEventListener("change", apply));
    featureChecks.forEach((check) => check.addEventListener("change", apply));
}

function initCustomDropdowns() {
    const selects = Array.from(document.querySelectorAll(".filter-grid select[data-filter]"));
    if (selects.length === 0) return;

    const wrappers = [];

    const closeAll = (exceptWrapper) => {
        wrappers.forEach((wrapper) => {
            if (wrapper !== exceptWrapper) wrapper.classList.remove("is-open");
        });
    };

    selects.forEach((select) => {
        if (select.dataset.customized === "1") return;
        select.dataset.customized = "1";
        select.classList.add("native-select-hidden");

        const wrapper = document.createElement("div");
        wrapper.className = "glass-select";

        const trigger = document.createElement("button");
        trigger.type = "button";
        trigger.className = "glass-select-trigger";
        trigger.setAttribute("aria-haspopup", "listbox");
        trigger.setAttribute("aria-expanded", "false");

        const label = document.createElement("span");
        label.className = "glass-select-label";
        const caret = document.createElement("span");
        caret.className = "glass-select-caret";
        caret.textContent = "\u2304";
        trigger.appendChild(label);
        trigger.appendChild(caret);

        const panel = document.createElement("div");
        panel.className = "glass-select-panel";
        const list = document.createElement("ul");
        list.className = "glass-select-list";
        list.setAttribute("role", "listbox");
        panel.appendChild(list);

        const setSelected = (value) => {
            select.value = value;
            const selectedOption = Array.from(select.options).find((option) => option.value === value);
            label.textContent = selectedOption ? selectedOption.textContent.trim() : "";

            Array.from(list.querySelectorAll(".glass-option")).forEach((btn) => {
                btn.classList.toggle("is-selected", btn.dataset.value === value);
            });
        };

        Array.from(select.options).forEach((option) => {
            const li = document.createElement("li");
            const optBtn = document.createElement("button");
            optBtn.type = "button";
            optBtn.className = "glass-option";
            optBtn.dataset.value = option.value;
            optBtn.textContent = option.textContent;
            if (option.disabled) optBtn.disabled = true;

            optBtn.addEventListener("click", () => {
                setSelected(option.value);
                wrapper.classList.remove("is-open");
                trigger.setAttribute("aria-expanded", "false");
                select.dispatchEvent(new Event("change", { bubbles: true }));
            });

            li.appendChild(optBtn);
            list.appendChild(li);
        });

        setSelected(select.value);

        trigger.addEventListener("click", () => {
            const willOpen = !wrapper.classList.contains("is-open");
            closeAll(wrapper);
            wrapper.classList.toggle("is-open", willOpen);
            trigger.setAttribute("aria-expanded", String(willOpen));
        });

        select.addEventListener("change", () => {
            setSelected(select.value);
        });

        wrapper.appendChild(trigger);
        wrapper.appendChild(panel);
        select.insertAdjacentElement("afterend", wrapper);
        wrappers.push(wrapper);
    });

    document.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof Element)) return;
        if (target.closest(".glass-select")) return;
        closeAll(null);
        wrappers.forEach((wrapper) => {
            const trigger = wrapper.querySelector(".glass-select-trigger");
            if (trigger) trigger.setAttribute("aria-expanded", "false");
        });
    });

    window.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;
        closeAll(null);
        wrappers.forEach((wrapper) => {
            const trigger = wrapper.querySelector(".glass-select-trigger");
            if (trigger) trigger.setAttribute("aria-expanded", "false");
        });
    });
}

function applyFilters(state) {
    const pins = Array.from(document.querySelectorAll(".pin"));
    const selectedType1 = getFilterValue("type1");
    const selectedType2 = getFilterValue("type2");
    const selectedSize = getFilterValue("size");
    const selectedEntrance = getFilterValue("entrance");
    const selectedUserRating = state.userFilterRating;
    const selectedAdminRating = state.adminFilterRating;
    const selectedFeatures = Array.from(document.querySelectorAll("input[data-feature]:checked")).map((c) => c.dataset.feature);

    let currentSelectionVisible = false;

    pins.forEach((pin) => {
        const matchesType1 = selectedType1 === "all" || pin.dataset.type1 === selectedType1;
        const matchesType2 = selectedType2 === "all" || pin.dataset.type2 === selectedType2;
        const matchesSize = selectedSize === "all" || pin.dataset.size === selectedSize;
        const matchesEntrance = selectedEntrance === "all" || pin.dataset.entrance === selectedEntrance;
        const userRatingValue = Math.round(Number(pin.dataset.userRating || 0));
        const adminRatingValue = Number(pin.dataset.adminRating || 0);
        const matchesUserRating = selectedUserRating === 0 || userRatingValue === selectedUserRating;
        const matchesAdminRating = selectedAdminRating === 0 || adminRatingValue === selectedAdminRating;
        const features = (pin.dataset.features || "").split(",");
        const matchesFeatures = selectedFeatures.every((feature) => features.includes(feature));
        const visible =
            matchesType1 &&
            matchesType2 &&
            matchesSize &&
            matchesEntrance &&
            matchesUserRating &&
            matchesAdminRating &&
            matchesFeatures;

        pin.classList.toggle("is-hidden", !visible);
        pin.classList.toggle("is-visible", visible);

        if (visible && pin.dataset.pinId === state.selectedPinId) {
            currentSelectionVisible = true;
        }
    });

    if (!currentSelectionVisible) {
        const firstVisible = pins.find((pin) => pin.classList.contains("is-visible"));
        if (firstVisible) {
            state.selectedPinId = firstVisible.dataset.pinId;
            pins.forEach((p) => p.classList.toggle("is-selected", p === firstVisible));
            renderSpot(state.selectedPinId, state);
        } else {
            state.selectedPinId = null;
            renderEmptySpotState();
        }
    }
}

function getFilterValue(name) {
    const control = document.querySelector(`select[data-filter='${name}']`);
    return control ? control.value : "all";
}

function renderSpot(pinId, state) {
    const spot = state.spotData[pinId];
    if (!spot) return;

    const title = document.querySelector("[data-spot-title]");
    const description = document.querySelector("[data-description-content]");
    const commentsList = document.querySelector("[data-comment-list]");

    if (title) title.textContent = spot.title;
    if (description) description.innerHTML = buildSpotDescription(spot);
    if (commentsList) {
        commentsList.innerHTML = "";
        spot.comments.forEach((comment) => {
            const li = document.createElement("li");
            const split = comment.split(":");
            li.innerHTML = `<strong>${escapeHtml(split[0])}:</strong> ${escapeHtml(split.slice(1).join(":").trim())}`;
            commentsList.appendChild(li);
        });
    }

    state.myRating = Number(spot.my_rating || 0);
    showSelectedSpotCoords(state);
    buildThumbs(spot.media, state);
    renderSpotActions(spot, state);
}

function initSpotActions(state) {
    const actions = document.querySelector("[data-spot-actions]");
    if (!actions) return;

    const likeButton = actions.querySelector("[data-like-btn]");
    const userRateRow = actions.querySelector("[data-user-rate-stars]");
    const isAuthenticated = actions.dataset.authenticated === "1";

    if (likeButton) {
        likeButton.addEventListener("click", async () => {
            if (!state.selectedPinId) return;
            if (!isAuthenticated) return;
            const url = buildSpotApiUrl(actions.dataset.likeUrlTemplate, state.selectedPinId);
            if (!url) return;

            const response = await postSpotAction(url, {});
            if (!response || !response.ok) return;

            const spot = state.spotData[state.selectedPinId];
            if (!spot) return;
            spot.likes_count = response.likes_count;
            spot.is_liked = response.is_liked;
            renderSpotActions(spot, state);
        });
    }

    if (userRateRow) {
        const stars = Array.from(userRateRow.querySelectorAll(".star"));
        stars.forEach((star) => {
            star.addEventListener("mouseenter", () => {
                paintStars(stars, Number(star.dataset.starValue), true);
            });
            star.addEventListener("click", async () => {
                if (!state.selectedPinId) return;
                if (!isAuthenticated) return;
                const selectedRating = Number(star.dataset.starValue);
                const url = buildSpotApiUrl(actions.dataset.rateUrlTemplate, state.selectedPinId);
                if (!url) return;
                const response = await postSpotAction(url, { rating: selectedRating });
                if (!response || !response.ok) return;

                const spot = state.spotData[state.selectedPinId];
                if (!spot) return;
                spot.my_rating = response.my_rating;
                spot.user_rating = response.user_rating;
                state.myRating = response.my_rating;
                updatePinUserRating(state.selectedPinId, response.user_rating);
                renderSpotActions(spot, state);
                if (state.userFilterRating !== 0) {
                    applyFilters(state);
                }
            });
        });

        userRateRow.addEventListener("mouseleave", () => {
            paintStars(stars, state.myRating, false);
        });
    }
}

function renderSpotActions(spot, state) {
    const actions = document.querySelector("[data-spot-actions]");
    if (!actions || !spot) return;
    const isAuthenticated = actions.dataset.authenticated === "1";

    const likeButton = actions.querySelector("[data-like-btn]");
    const likeCount = actions.querySelector("[data-like-count]");
    const likeLabel = actions.querySelector("[data-like-btn-label]");
    const userRateRow = actions.querySelector("[data-user-rate-stars]");

    if (likeButton) {
        likeButton.disabled = !isAuthenticated;
        likeButton.classList.toggle("is-active", Boolean(spot.is_liked));
    }
    if (likeCount) likeCount.textContent = String(spot.likes_count ?? 0);
    if (likeLabel) {
        const labels = getUiLabels(getPageLanguage());
        likeLabel.textContent = labels.like;
    }
    if (userRateRow) {
        const stars = Array.from(userRateRow.querySelectorAll(".star"));
        const myRating = Number(spot.my_rating || 0);
        state.myRating = myRating;
        paintStars(stars, myRating, false);
        stars.forEach((star) => {
            star.disabled = !isAuthenticated;
        });
    }
}

function buildSpotApiUrl(template, spotSlug) {
    if (!template || !spotSlug) return "";
    return template.replace("__spot_slug__", spotSlug);
}

async function postSpotAction(url, payload) {
    try {
        const body = new URLSearchParams(payload);
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            },
            body: body.toString(),
        });
        if (!response.ok) return null;
        return await response.json();
    } catch (error) {
        return null;
    }
}

function updatePinUserRating(pinId, value) {
    const pin = document.querySelector(`.pin[data-pin-id="${pinId}"]`);
    if (!pin) return;
    pin.dataset.userRating = String(value || 0);
}

function buildThumbs(mediaItems, state) {
    const thumbStrip = document.querySelector("[data-thumb-strip]");
    const mainMedia = document.querySelector("[data-main-media]");
    const mediaEmpty = document.querySelector("[data-media-empty]");
    const mediaSlider = document.querySelector("[data-media-slider]");
    if (!thumbStrip || !mainMedia) return;

    const normalized = normalizeMediaItems(mediaItems);
    state.mediaItems = normalized;
    state.mediaIndex = 0;

    thumbStrip.innerHTML = "";
    const labels = getUiLabels(getPageLanguage());
    if (normalized.length === 0) {
        if (mediaSlider) mediaSlider.hidden = true;
        if (mediaEmpty) mediaEmpty.hidden = false;
        mainMedia.textContent = labels.noMedia;
        updateMediaControls(state);
        return;
    }

    if (mediaSlider) mediaSlider.hidden = false;
    if (mediaEmpty) mediaEmpty.hidden = true;

    normalized.forEach((mediaItem, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "thumb";
        button.innerHTML = `
            ${
                mediaItem.thumb
                    ? `<img src="${escapeAttribute(mediaItem.thumb)}" alt="${escapeAttribute(mediaItem.title || "")}" class="thumb-image">`
                    : `<span class="thumb-fallback">${mediaItem.type === "video" ? labels.video : labels.image}</span>`
            }
            ${mediaItem.type === "video" ? '<span class="thumb-video-badge">&#9658;</span>' : ""}
        `;
        button.setAttribute("aria-label", mediaItem.title || `${mediaItem.type} ${index + 1}`);
        button.dataset.mediaIndex = String(index);
        if (index === 0) button.classList.add("is-active");

        button.addEventListener("click", () => {
            state.mediaIndex = index;
            renderMainMedia(mainMedia, state.mediaItems[state.mediaIndex]);
            updateMediaControls(state);
        });

        thumbStrip.appendChild(button);
    });

    renderMainMedia(mainMedia, state.mediaItems[0]);
    updateMediaControls(state);
}

function initMediaSlider(state) {
    const mainMedia = document.querySelector("[data-main-media]");
    const navButtons = Array.from(document.querySelectorAll("[data-media-nav]"));
    const thumbScrollButtons = Array.from(document.querySelectorAll("[data-thumb-scroll]"));
    const thumbStrip = document.querySelector("[data-thumb-strip]");
    if (!mainMedia) return;

    navButtons.forEach((button) => {
        button.addEventListener("click", () => {
            if (state.mediaItems.length === 0) return;
            if (button.dataset.mediaNav === "prev") {
                state.mediaIndex =
                    (state.mediaIndex - 1 + state.mediaItems.length) % state.mediaItems.length;
            } else {
                state.mediaIndex = (state.mediaIndex + 1) % state.mediaItems.length;
            }
            renderMainMedia(mainMedia, state.mediaItems[state.mediaIndex]);
            updateMediaControls(state);
        });
    });

    thumbScrollButtons.forEach((button) => {
        button.addEventListener("click", () => {
            if (!thumbStrip) return;
            const offset = Math.max(180, thumbStrip.clientWidth * 0.7);
            const direction = button.dataset.thumbScroll === "prev" ? -1 : 1;
            thumbStrip.scrollBy({ left: direction * offset, behavior: "smooth" });
        });
    });
}

function updateMediaControls(state) {
    const thumbStrip = document.querySelector("[data-thumb-strip]");
    const navButtons = Array.from(document.querySelectorAll("[data-media-nav]"));
    if (!thumbStrip) return;

    const thumbs = Array.from(thumbStrip.querySelectorAll(".thumb"));
    thumbs.forEach((thumb, index) => {
        thumb.classList.toggle("is-active", index === state.mediaIndex);
    });

    const activeThumb = thumbs[state.mediaIndex];
    if (activeThumb) {
        activeThumb.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
    }

    const hasMedia = state.mediaItems.length > 0;
    navButtons.forEach((button) => {
        button.disabled = !hasMedia;
    });
}

function normalizeMediaItems(mediaItems) {
    if (!Array.isArray(mediaItems)) return [];
    return mediaItems
        .filter((item) => item && item.src)
        .map((item) => ({
            type: item.type === "video" ? "video" : "image",
            src: String(item.src),
            thumb: item.thumb ? String(item.thumb) : "",
            title: item.title ? String(item.title) : "",
        }));
}

function initMapCursorCoords(state) {
    const mapCanvas = document.querySelector("[data-map-canvas]");
    if (!mapCanvas) return;

    mapCanvas.addEventListener("mousemove", (event) => {
        const rect = mapCanvas.getBoundingClientRect();
        const xPercent = clamp(((event.clientX - rect.left) / rect.width) * 100, 0, 100);
        const yPercent = clamp(((event.clientY - rect.top) / rect.height) * 100, 0, 100);
        updateCoordsLabel(`${xPercent.toFixed(1)} / ${yPercent.toFixed(1)}`);
    });

    mapCanvas.addEventListener("mouseleave", () => {
        showSelectedSpotCoords(state);
    });
}

function showSelectedSpotCoords(state) {
    const spot = state.selectedPinId ? state.spotData[state.selectedPinId] : null;
    updateCoordsLabel(spot && spot.coords ? spot.coords : "0.0 / 0.0");
}

function updateCoordsLabel(value) {
    const label = document.querySelector(".coords-label");
    if (!label) return;
    const labels = getUiLabels(getPageLanguage());
    label.textContent = `${labels.coords}: ${value}`;
}

function applyMapTransform(canvas, state) {
    canvas.style.transform = `translate(${state.panX}px, ${state.panY}px) scale(${state.zoom})`;
    updatePinScale(state.zoom);
}

function zoomAtPoint(state, canvas, pointX, pointY, nextZoom) {
    const prevZoom = state.zoom;
    if (prevZoom === nextZoom) return;

    state.panX = pointX - ((pointX - state.panX) * nextZoom) / prevZoom;
    state.panY = pointY - ((pointY - state.panY) * nextZoom) / prevZoom;
    state.zoom = nextZoom;
    applyMapTransform(canvas, state);
}

function centerMapInFrame(state, frame) {
    const rect = frame.getBoundingClientRect();
    state.panX = (rect.width - rect.width * state.zoom) / 2;
    state.panY = (rect.height - rect.height * state.zoom) / 2;
}

function updatePinScale(zoom) {
    const pins = document.querySelectorAll(".pin");
    const normalizedZoom = Math.max(zoom, 0.0001);
    const adaptiveScale = clamp(1 / Math.pow(normalizedZoom, 0.75), 0.35, 1.25) * 0.7;
    pins.forEach((pin) => {
        pin.style.setProperty("--pin-scale", adaptiveScale.toFixed(4));
    });
}

function initMediaLightbox(state) {
    const mainMedia = document.querySelector("[data-main-media]");
    if (!mainMedia) return;

    const lightbox = ensureMediaLightbox(state);
    if (!lightbox) return;

    mainMedia.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof Element)) return;
        if (!target.closest("[data-open-lightbox]")) return;

        const mediaItem = state.mediaItems[state.mediaIndex];
        if (!mediaItem) return;
        openMediaLightbox(lightbox, state, state.mediaIndex);
    });
}

function ensureMediaLightbox(state) {
    let lightbox = document.querySelector("[data-media-lightbox]");
    if (lightbox) return lightbox;

    lightbox = document.createElement("div");
    lightbox.className = "media-lightbox";
    lightbox.setAttribute("data-media-lightbox", "");
    lightbox.hidden = true;
    lightbox.innerHTML = `
        <button class="media-lightbox-backdrop" type="button" data-lightbox-close aria-label="Close preview"></button>
        <div class="media-lightbox-dialog" role="dialog" aria-modal="true">
            <button class="media-lightbox-nav media-lightbox-nav-prev" type="button" data-lightbox-nav="prev" aria-label="Previous media">&#10094;</button>
            <button class="media-lightbox-nav media-lightbox-nav-next" type="button" data-lightbox-nav="next" aria-label="Next media">&#10095;</button>
            <button class="media-lightbox-close" type="button" data-lightbox-close aria-label="Close preview">x</button>
            <div class="media-lightbox-content" data-lightbox-content></div>
        </div>
    `;

    document.body.appendChild(lightbox);

    lightbox.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof Element)) return;
        const navBtn = target.closest("[data-lightbox-nav]");
        if (navBtn) {
            if (state.mediaItems.length <= 1) return;
            const direction = navBtn.getAttribute("data-lightbox-nav") === "prev" ? -1 : 1;
            state.mediaIndex = (state.mediaIndex + direction + state.mediaItems.length) % state.mediaItems.length;
            renderMediaLightboxContent(lightbox, state.mediaItems[state.mediaIndex]);
            return;
        }
        if (!target.closest("[data-lightbox-close]")) return;
        closeMediaLightbox(lightbox);
    });

    window.addEventListener("keydown", (event) => {
        if (lightbox.hidden) return;
        if (event.key === "Escape") {
            closeMediaLightbox(lightbox);
            return;
        }
        if ((event.key === "ArrowLeft" || event.key === "ArrowRight") && state.mediaItems.length > 1) {
            const direction = event.key === "ArrowLeft" ? -1 : 1;
            state.mediaIndex = (state.mediaIndex + direction + state.mediaItems.length) % state.mediaItems.length;
            renderMediaLightboxContent(lightbox, state.mediaItems[state.mediaIndex]);
        }
    });

    return lightbox;
}

function openMediaLightbox(lightbox, state, startIndex) {
    if (!Array.isArray(state.mediaItems) || state.mediaItems.length === 0) return;
    state.mediaIndex = clamp(Number(startIndex) || 0, 0, state.mediaItems.length - 1);
    const mediaItem = state.mediaItems[state.mediaIndex];
    renderMediaLightboxContent(lightbox, mediaItem);
    const navButtons = Array.from(lightbox.querySelectorAll("[data-lightbox-nav]"));
    const showNav = state.mediaItems.length > 1;
    navButtons.forEach((btn) => {
        btn.hidden = !showNav;
    });
    lightbox.hidden = false;
    lightbox.classList.add("is-open");
    document.body.classList.add("is-lightbox-open");
}

function renderMediaLightboxContent(lightbox, mediaItem) {
    const content = lightbox.querySelector("[data-lightbox-content]");
    if (!content) return;
    if (!mediaItem) {
        content.innerHTML = "";
        return;
    }

    const safeSrc = escapeAttribute(mediaItem.src);
    const safeTitle = escapeAttribute(mediaItem.title || "");

    if (mediaItem.type === "video") {
        const safeThumb = escapeAttribute(mediaItem.thumb || "");
        content.innerHTML = `
            <div class="media-lightbox-media-shell is-loading" data-lightbox-media-shell>
                <div class="media-lightbox-loading" data-lightbox-loading>
                    ${
                        safeThumb
                            ? `<img class="media-lightbox-loading-thumb" src="${safeThumb}" alt="">`
                            : `<div class="media-lightbox-loading-fallback"></div>`
                    }
                    <span class="media-lightbox-spinner" aria-hidden="true"></span>
                </div>
                <video class="media-lightbox-video" preload="metadata" playsinline controlslist="nofullscreen noremoteplayback nodownload" disablepictureinpicture>
                    <source src="${safeSrc}">
                </video>
            </div>
        `;
        const shell = content.querySelector("[data-lightbox-media-shell]");
        const video = content.querySelector(".media-lightbox-video");
        if (video) {
            const onReady = () => {
                if (shell) shell.classList.remove("is-loading");
                video.setAttribute("controls", "");
            };
            const onError = () => {
                if (shell) shell.classList.remove("is-loading");
                const loading = content.querySelector("[data-lightbox-loading]");
                if (loading) loading.innerHTML = '<span class="media-lightbox-error">Video unavailable</span>';
            };
            video.addEventListener("canplay", onReady, { once: true });
            video.addEventListener("error", onError, { once: true });
        }
    } else {
        content.innerHTML = `
            <div class="media-lightbox-media-shell">
                <img class="media-lightbox-image" src="${safeSrc}" alt="${safeTitle}">
            </div>
        `;
    }
}

function closeMediaLightbox(lightbox) {
    const content = lightbox.querySelector("[data-lightbox-content]");
    if (content) content.innerHTML = "";
    lightbox.classList.remove("is-open");
    lightbox.hidden = true;
    document.body.classList.remove("is-lightbox-open");
}

function getSpotDataFromPage() {
    const scriptNode = document.getElementById("spot-data-json");
    if (!scriptNode) return {};
    try {
        return JSON.parse(scriptNode.textContent);
    } catch (error) {
        return {};
    }
}

function buildSpotDescription(spot) {
    const labels = getUiLabels(getPageLanguage());
    const features = Array.isArray(spot.features) && spot.features.length > 0 ? spot.features.join(", ") : labels.none;
    if (spot.kind === "place") {
        return `
            <strong>${labels.name}:</strong> ${escapeHtml(spot.title)}<br>
            <strong>${labels.coords}:</strong> ${escapeHtml(spot.coords)}<br>
            <strong>${labels.type}:</strong> ${escapeHtml(spot.type_name)}<br>
            <strong>${labels.resources}:</strong> ${escapeHtml(String(spot.resources ?? "-"))}<br>
            <strong>${labels.features}:</strong> ${escapeHtml(features)}<br>
            <strong>${labels.adminRating}:</strong> ${escapeHtml(String(spot.admin_rating))}<br>
            <strong>${labels.usersRating}:</strong> ${escapeHtml(String(Number(spot.user_rating || 0).toFixed(2)))}<br>
            <strong>${labels.addedBy}:</strong> ${escapeHtml(String(spot.player))}
        `;
    }
    return `
        <strong>${labels.name}:</strong> ${escapeHtml(spot.title)}<br>
        <strong>${labels.coords}:</strong> ${escapeHtml(spot.coords)}<br>
        <strong>${labels.type}:</strong> ${escapeHtml(spot.type_name)}<br>
        <strong>${labels.type}:</strong> ${escapeHtml(spot.sl_name)}<br>
        <strong>${labels.maxDino}:</strong> ${escapeHtml(String(spot.dino_name))}<br>
        <strong>${labels.exitQty}:</strong> ${escapeHtml(String(spot.exit_quantity))}<br>
        <strong>${labels.features}:</strong> ${escapeHtml(features)}<br>
        <strong>${labels.adminRating}:</strong> ${escapeHtml(String(spot.admin_rating))}<br>
        <strong>${labels.usersRating}:</strong> ${escapeHtml(String(Number(spot.user_rating || 0).toFixed(2)))}<br>
        <strong>${labels.addedBy}:</strong> ${escapeHtml(String(spot.player))}
    `;
}

function renderEmptySpotState() {
    const labels = getUiLabels(getPageLanguage());
    const title = document.querySelector("[data-spot-title]");
    const description = document.querySelector("[data-description-content]");
    const comments = document.querySelector("[data-comment-list]");
    const media = document.querySelector("[data-main-media]");
    const mediaEmpty = document.querySelector("[data-media-empty]");
    const mediaSlider = document.querySelector("[data-media-slider]");
    const thumbStrip = document.querySelector("[data-thumb-strip]");
    const likeCount = document.querySelector("[data-like-count]");
    const likeButton = document.querySelector("[data-like-btn]");
    const userRateRow = document.querySelector("[data-user-rate-stars]");
    if (title) title.textContent = labels.noSpots;
    if (description) description.textContent = labels.noSpotsByFilter;
    if (comments) comments.innerHTML = "";
    if (media) media.textContent = labels.noMedia;
    if (thumbStrip) thumbStrip.innerHTML = "";
    if (mediaSlider) mediaSlider.hidden = true;
    if (mediaEmpty) mediaEmpty.hidden = false;
    if (likeCount) likeCount.textContent = "0";
    if (likeButton) likeButton.classList.remove("is-active");
    if (userRateRow) {
        paintStars(Array.from(userRateRow.querySelectorAll(".star")), 0, false);
    }
    updateCoordsLabel("0.0 / 0.0");
}

function getPageLanguage() {
    const scriptNode = document.getElementById("language-code-json");
    if (scriptNode) {
        try {
            return JSON.parse(scriptNode.textContent);
        } catch (error) {
            return document.documentElement.lang || "en";
        }
    }
    return document.documentElement.lang || "en";
}

function getUiLabels(language) {
    const isRu = String(language).toLowerCase().startsWith("ru");
    if (isRu) {
        return {
            video: "\u0412\u0438\u0434\u0435\u043e",
            image: "\u0418\u0437\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u0435",
            none: "\u041d\u0435\u0442",
            name: "\u0418\u043c\u044f",
            coords: "\u041a\u043e\u043e\u0440\u0434\u0438\u043d\u0430\u0442\u044b",
            type: "\u0422\u0438\u043f",
            maxDino: "\u041b\u0443\u0447\u0448\u0438\u0439 \u0434\u0438\u043d\u043e \u0434\u043b\u044f \u0440\u0435\u0439\u0434\u0430",
            exitQty: "\u041a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e \u0432\u0445\u043e\u0434\u043e\u0432",
            resources: "\u0420\u0435\u0441\u0443\u0440\u0441\u044b",
            features: "\u0424\u0438\u0448\u043a\u0438",
            adminRating: "\u0420\u0435\u0439\u0442\u0438\u043d\u0433 \u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0430\u0442\u043e\u0440\u0430",
            usersRating: "\u0420\u0435\u0439\u0442\u0438\u043d\u0433 \u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439",
            like: "\u041b\u0430\u0439\u043a",
            addedBy: "\u0414\u043e\u0431\u0430\u0432\u043b\u0435\u043d",
            noSpots: "\u041d\u0435\u0442 \u0441\u043f\u043e\u0442\u043e\u0432",
            noSpotsByFilter: "\u041d\u0435\u0442 \u0441\u043f\u043e\u0442\u043e\u0432 \u043f\u043e\u0434 \u0442\u0435\u043a\u0443\u0449\u0438\u0435 \u0444\u0438\u043b\u044c\u0442\u0440\u044b.",
            noMedia: "\u041d\u0435\u0442 \u043c\u0435\u0434\u0438\u0430",
        };
    }
    return {
        video: "Video",
        image: "Image",
        none: "None",
        name: "Name",
        coords: "Coords",
        type: "Type",
        maxDino: "Best dino for raid",
        exitQty: "Exit Quantity",
        resources: "Resources",
        features: "Features",
        adminRating: "Admin Priority Rating",
        usersRating: "Users Priority Rating",
        like: "Like",
        addedBy: "Added by",
        noSpots: "No spots",
        noSpotsByFilter: "No spots match the current filters.",
        noMedia: "No media",
    };
}

function getRatingColor(rating) {
    const colorMap = {
        1: "#2ebc62",
        2: "#3b7fdc",
        3: "#8751d6",
        4: "#d6c245",
        5: "#36c7db",
    };
    return colorMap[rating] || "#758194";
}

function renderMainMedia(container, mediaItem) {
    if (!container || !mediaItem) return;
    const safeSrc = escapeAttribute(mediaItem.src);
    const safeTitle = escapeAttribute(mediaItem.title || "");

    if (mediaItem.type === "video") {
        container.innerHTML = `
            <video class="media-video" data-open-lightbox="1" controls preload="metadata" playsinline controlslist="nofullscreen noremoteplayback nodownload" disablepictureinpicture>
                <source src="${safeSrc}">
            </video>
            <span class="media-badge">VIDEO</span>
        `;
        return;
    }

    container.innerHTML = `<img class="media-image" data-open-lightbox="1" src="${safeSrc}" alt="${safeTitle}">`;
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function escapeAttribute(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function getCookie(name) {
    const cookieValue = document.cookie
        .split(";")
        .map((item) => item.trim())
        .find((item) => item.startsWith(`${name}=`));
    return cookieValue ? decodeURIComponent(cookieValue.split("=")[1]) : "";
}

function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
}
