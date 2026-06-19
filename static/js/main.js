console.log("TravelWise Loaded");

setTimeout(() => {

let alerts =
document.querySelectorAll(".alert");

alerts.forEach(alert => {

let bsAlert =
new bootstrap.Alert(alert);

bsAlert.close();

});

},5000);
function togglePassword(id){

    let field =
    document.getElementById(id);

    let button =
    event.currentTarget;

    let icon =
    button.querySelector("i");

    if(field.type === "password"){

        field.type = "text";

        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");

    }

    else{

        field.type = "password";

        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");

    }

}
