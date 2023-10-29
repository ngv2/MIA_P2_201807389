function executeCommand() {
    document.getElementById("consoleOutputLabel").innerHTML = "";
    var e = {
        commands: document.getElementById("commandTextArea").value
    };
    fetch(back_host + "/ejecutar", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(e)
    }).then((e => e.json())).then((e => {
        console.log(e), document.getElementById("consoleOutputLabel").innerHTML = e.console_output.replace(/\n/g, "<br>")
    })).catch((e => console.error(e)))
}

function readFile(e) {
    const n = e.target.files[0],
        t = new FileReader;
    t.onload = function(e) {
        const n = e.target.result;
        console.log(n), document.getElementById("commandTextArea").value = n
    }, t.readAsText(n)
}