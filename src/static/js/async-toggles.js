function getCookie(name) {
  const cookieValue = document.cookie
    .split(";")
    .map((c) => c.trim())
    .find((c) => c.startsWith(name + "="));
  if (!cookieValue) return "";
  return decodeURIComponent(cookieValue.split("=").slice(1).join("="));
}

async function submitAsyncToggle(input) {
  const url = input.dataset.toggleUrl;
  if (!url) return;

  const previousChecked = !input.checked;
  const csrfToken = getCookie("csrftoken");
  const body = new URLSearchParams();
  body.set("enabled", input.checked ? "true" : "false");

  input.disabled = true;
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": csrfToken,
        Accept: "application/json",
      },
      body: body.toString(),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      input.checked = previousChecked;
      if (data && data.error) {
        window.alert(data.error);
      }
      return;
    }
    if (typeof data.enabled === "boolean") {
      input.checked = data.enabled;
    }
  } catch (error) {
    input.checked = previousChecked;
    window.alert("Failed to update setting. Please try again.");
  } finally {
    input.disabled = false;
  }
}

window.addEventListener("DOMContentLoaded", () => {
  const toggleInputs = document.querySelectorAll("input[data-async-toggle='true']");
  toggleInputs.forEach((input) => {
    input.addEventListener("change", () => submitAsyncToggle(input));
  });
});
