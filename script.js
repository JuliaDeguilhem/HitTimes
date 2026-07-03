const decadeData = {
  1980: {
    year: "Année 1980",
    title: "Le son cassette",
    copy:
      "Des titres culte à reconnaître vite, portés par une identité bleu pastel inspirée des supports analogiques.",
    challenge: "Retrouver l'artiste ou le groupe.",
    points: "+2 cases si la réponse est juste.",
  },
  1990: {
    year: "Année 1990",
    title: "Le réflexe vinyle",
    copy:
      "Une décennie jaune rétro, pensée pour raviver les classiques et les refrains que tout le monde reprend.",
    challenge: "Trouver le titre de la chanson.",
    points: "+3 cases pour une réponse complète.",
  },
  2000: {
    year: "Année 2000",
    title: "Le lecteur nomade",
    copy:
      "Le vert sauge rassemble les tubes du passage au numérique et les souvenirs de playlists partagées.",
    challenge: "Situer l'année à deux ans près.",
    points: "+1 case pour garder le rythme.",
  },
  2010: {
    year: "Année 2010",
    title: "L'écoute en continu",
    copy:
      "Le rose poudré fait entrer les hits récents dans la partie, entre défis rapides et culture pop.",
    challenge: "Donner l'année exacte.",
    points: "+4 cases pour les plus précis.",
  },
};

const stage = document.querySelector(".decade-stage");
const decadeCard = document.querySelector(".decade-card");
const tabs = document.querySelectorAll(".decade-tab");
const year = document.querySelector("#decade-year");
const title = document.querySelector("#decade-title");
const copy = document.querySelector("#decade-copy");
const challenge = document.querySelector("#decade-challenge");
const points = document.querySelector("#decade-points");

requestAnimationFrame(() => {
  document.body.classList.add("is-ready");
});

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const decade = tab.dataset.decade;
    const data = decadeData[decade];

    tabs.forEach((item) => {
      const isCurrent = item === tab;
      item.classList.toggle("is-active", isCurrent);
      item.setAttribute("aria-selected", String(isCurrent));
    });

    stage.dataset.current = decade;
    year.textContent = data.year;
    title.textContent = data.title;
    copy.textContent = data.copy;
    challenge.textContent = data.challenge;
    points.textContent = data.points;

    decadeCard.classList.remove("is-switching");
    void decadeCard.offsetWidth;
    decadeCard.classList.add("is-switching");
  });

  tab.addEventListener("keydown", (event) => {
    const tabArray = Array.from(tabs);
    const currentIndex = tabArray.indexOf(tab);
    const direction = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;

    if (!direction) return;

    event.preventDefault();
    const nextIndex = (currentIndex + direction + tabArray.length) % tabArray.length;
    tabArray[nextIndex].focus();
    tabArray[nextIndex].click();
  });
});

const revealItems = document.querySelectorAll(
  ".section, .intro-band p, .quick-facts li, .steps article, .gallery-item, .score-list article"
);

if ("IntersectionObserver" in window) {
  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        revealObserver.unobserve(entry.target);
      });
    },
    { threshold: 0.14 }
  );

  revealItems.forEach((item) => {
    item.classList.add("reveal");
    revealObserver.observe(item);
  });
} else {
  revealItems.forEach((item) => item.classList.add("is-visible"));
}

const navLinks = document.querySelectorAll("nav a[href^='#']");
const navSections = Array.from(navLinks)
  .map((link) => document.querySelector(link.getAttribute("href")))
  .filter(Boolean);

if ("IntersectionObserver" in window) {
  const navObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;

        navLinks.forEach((link) => {
          link.classList.toggle("is-active", link.getAttribute("href") === `#${entry.target.id}`);
        });
      });
    },
    { rootMargin: "-38% 0px -52% 0px" }
  );

  navSections.forEach((section) => navObserver.observe(section));
}

const demoButton = document.querySelector(".demo-button");
const demoPlayer = document.querySelector(".demo-player");
const demoLabel = document.querySelector(".demo-label");
const demoStatus = document.querySelector(".demo-status");
const demoDecades = ["Année 1980", "Année 1990", "Année 2000", "Année 2010"];
let demoIndex = 1;
let demoTimer;

demoButton?.addEventListener("click", () => {
  window.clearTimeout(demoTimer);
  demoIndex = (demoIndex + 1) % demoDecades.length;

  demoLabel.textContent = demoDecades[demoIndex];
  demoStatus.textContent = "Extrait en cours";
  demoButton.setAttribute("aria-pressed", "true");
  demoPlayer.classList.remove("is-playing");
  void demoPlayer.offsetWidth;
  demoPlayer.classList.add("is-playing");

  demoTimer = window.setTimeout(() => {
    demoStatus.textContent = "Réponse révélée : titre, artiste, année";
    demoButton.setAttribute("aria-pressed", "false");
  }, 3200);
});
