document.addEventListener("DOMContentLoaded", ()=> {
    let register_button = document.getElementById("reg_button");
    let register_form = document.getElementById("reg_form");
    let login_button = document.getElementById("login_button");
    let login_form = document.getElementById("login_form");

    register_button.addEventListener('click', ()=> {
        register_form.style.display = "block";
        login_form.style.display = "none";
    }, false)
    login_button.addEventListener('click', ()=> {
        register_form.style.display = "none";
        login_form.style.display = "block";
    }, false)
}, false)