const signupForm = document.getElementById("signupform");/*document refers to whole web page and serached for one specific element */
if (signupForm) {/*only checks if the following element exist inthe page */
  signupForm.addEventListener("submit", async function(event) {/* runs when ever the form sunmitted async means function allowed to use await inside itneed beause network request take time and we dont want to pause the page while waiting*/
    event.preventDefault();/*helps not to refresh the page while submitting the html for  */

    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;/*value hold the user input */
    const phone = document.getElementById("phone").value;
    const password = document.getElementById("password").value;
    const confirmpassword = document.getElementById("confirmpassword").value;

    if (password !== confirmpassword) {
      alert("Passwords do not match!");/* client side checks*/
      return;
    }
    /**here i sm sending the data to python */
    /*fetch sends a http request to your flask server to the signup route in app.py @app.route is the network call */
    const response = await fetch("/api/signup", {/*actual network request */
      method: "POST", 
      headers: {
        "Content-Type": "application/json"/** tells the server the body i am sending a json text so flask know to change it */
      },
      body: JSON.stringify({/**take a java script object and converts it to json text string this is the structure that travel to over the network */
        name: name,
        email: email,
        phone: phone,
        password: password,
      })
    });

    const data = await response.json();/**pauses the function untill the response actuall arrives then continues */

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