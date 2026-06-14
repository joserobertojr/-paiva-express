const menuButton = document.querySelector(".menu-toggle");
const nav = document.querySelector(".nav");
const form = document.querySelector(".lead-form");
const storeWhatsApp = "5583998824626";

menuButton?.addEventListener("click", () => {
  if (!nav) return;

  const isOpen = nav.classList.toggle("is-open");
  menuButton.setAttribute("aria-expanded", String(isOpen));
});

nav?.addEventListener("click", (event) => {
  if (event.target instanceof HTMLAnchorElement) {
    nav.classList.remove("is-open");
    menuButton?.setAttribute("aria-expanded", "false");
  }
});

form?.addEventListener("submit", (event) => {
  event.preventDefault();

  const data = new FormData(form);
  const nome = data.get("nome") || "";
  const modelo = data.get("modelo") || "";
  const pagamento = data.get("pagamento") || "";
  const mensagem = `Olá, Apple House. Sou ${nome}. Tenho interesse em ${modelo} e quero simular: ${pagamento}.`;
  const url = `https://wa.me/${storeWhatsApp}?text=${encodeURIComponent(mensagem)}`;

  window.open(url, "_blank", "noopener");
});
