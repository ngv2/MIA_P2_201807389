function makeLogin() {
    event.preventDefault();
    var e = document.getElementById("usernameInput").value,
        o = document.getElementById("passwordInput").value,
        n = document.getElementById("idInput").value;
    console.log("iniciando sesion con user " + e + ", pass:" + o + ", id:" + n);
    var t = {
        commands: `login -user=${e} -pass=${o} -id=${n}`
    };
    fetch(back_host + "/ejecutar", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(t)
    }).then((e => e.json())).then((e => {
        console.log(e.console_output), e.console_output.match(/(INICIO DE SESIÓN CON ÉXITO)/) != null ? (console.log("Inicio correcto"), alert("Inicio correcto"), window.location.href = "reportes.html") : alert(e.console_output)
    })).catch((e => console.error(e)))
}