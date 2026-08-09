const signupForm = document.getElementById("signupform");
if (signupForm) {
  signupForm.addEventListener("submit", async function(event) {
    event.preventDefault();

    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const phone = document.getElementById("phone").value;
    const password = document.getElementById("password").value;
    const confirmpassword = document.getElementById("confirmpassword").value;

    if (password !== confirmpassword) {
      alert("Passwords do not match!");
      return;
    }

    const response = await fetch("/api/signup", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        name: name,
        email: email,
        phone: phone,
        password: password,
      })
    });

    const data = await response.json();

    if (response.ok) {
      alert("Account created successfully!");
      window.location.href = "/login";
    } else {
      alert(data.message);
    }
  });
}
/*LOGIN VALIDATION*/
const loginForm = document.getElementById("loginform");
if (loginForm) {
  loginForm.addEventListener("submit", async function(event) {
    event.preventDefault();

    const identifier = document.getElementById("identifier").value;
    const password = document.getElementById("password").value;
    const remember = document.getElementById("remember").checked;

    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier, password, remember })
    });

    const data = await response.json();

    if (response.ok) {
      window.location.href = "/dashboard";
    } else {
      alert(data.message);
    }
  });
}