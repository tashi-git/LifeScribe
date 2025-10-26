const baseURL = "http://127.0.0.1:5000/api";
let currentUserId = null;

document.addEventListener("DOMContentLoaded", () => {
  const loginSection = document.getElementById("login-section");
  const registerSection = document.getElementById("register-section");
  const diarySection = document.getElementById("diary-section");

  // Set initial title
  document.getElementById("title").textContent = "Login";

  document.getElementById("show-register").onclick = () => {
    loginSection.style.display = "none";
    registerSection.style.display = "block";
    document.getElementById("title").textContent = "Registration";
  };

  document.getElementById("show-login").onclick = () => {
    registerSection.style.display = "none";
    loginSection.style.display = "block";
    document.getElementById("title").textContent = "Login";
  };

  // Register button
  document.getElementById("register-btn").onclick = async () => {
    const username = document.getElementById("register-username").value;
    const email = document.getElementById("register-email").value;
    const password = document.getElementById("register-password").value;

    const res = await fetch(`${baseURL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password })
    });
    const data = await res.json();

    alert(data.status === "success" ? "Registration successful!" : data.message);
    if (data.status === "success") {
      // Clear register form
      document.getElementById("register-username").value = "";
      document.getElementById("register-email").value = "";
      document.getElementById("register-password").value = "";
      // Redirect to login section
      registerSection.style.display = "none";
      loginSection.style.display = "block";
    }
  };

  // Login button
  document.getElementById("login-btn").onclick = async () => {
    const username = document.getElementById("login-username").value;
    const password = document.getElementById("login-password").value;

    const res = await fetch(`${baseURL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();

    if (data.status === "success") {
      currentUserId = data.user_id;
      loginSection.style.display = "none";
      diarySection.style.display = "block";
      loadEntries();
    } else {
      alert(data.message);
    }
  };

  // Save diary entry
  document.getElementById("save-entry-btn").onclick = async () => {
    const content = document.getElementById("diary-text").value;
    if (!content.trim()) return alert("Write something first!");

    await fetch(`${baseURL}/entry`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: currentUserId, content })
    });

    document.getElementById("diary-text").value = "";
    loadEntries();
  };

  // Logout
  document.getElementById("logout-btn").onclick = () => {
    currentUserId = null;
    diarySection.style.display = "none";
    loginSection.style.display = "block";
  };
});

async function loadEntries() {
  const res = await fetch(`${baseURL}/entries/${currentUserId}`);
  const entries = await res.json();
  const entriesDiv = document.getElementById("entries");

  entriesDiv.innerHTML = "";
  entries.forEach(e => {
    const div = document.createElement("div");
    div.className = "entry";
    div.innerHTML = `<p>${e.content}</p><small>${e.created_at}</small>`;
    entriesDiv.appendChild(div);
  });
}
