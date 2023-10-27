function viewImage(e) {
    console.log("Viewing image with path: " + e);

    document.getElementById("viewerDiv").innerHTML = "";

    if (e.endsWith(".txt")) {
        console.log("Haciendo txt con texto:")
        console.log(e)
        fetch(back_host + "/obtener_reporte", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                path: e
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log(data)
            const divElement = document.createElement("div");
            divElement.innerHTML = data.Content.replace(/\n/g, "<br>");
            document.getElementById("viewerDiv").appendChild(divElement);
        });
    } else {
        fetch(back_host + "/obtener_reporte", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                path: e
            })
        })
        .then(response => response.text())
        .then(imageData => {
            console.log(imageData)
            const imgElement = document.createElement("img");
            const imageSource = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(imageData)}`;
            imgElement.setAttribute("src", imageSource);

            window.open().document.write(imgElement.outerHTML);

            imgElement.addEventListener("click", function() {
                window.open().document.write(imgElement.outerHTML);
            });

            document.getElementById("viewerDiv").appendChild(imgElement);
        });
    }
}
fetch(back_host + "/lista_reportes").then((e => e.json())).then((e => {
    console.log(e);
    var t = [];
    if (e.list === "") {
        var n = document.getElementById("dataTable").getElementsByTagName("tbody")[0];

        var i = n.insertRow(o);

        i.insertCell(0).innerHTML = "-";

        var r = i.insertCell(1);
        r.innerHTML = "-";
    }
    for (const n of e.list.split("\n")) t.push(n), console.log(n);
    for (var n = document.getElementById("dataTable").getElementsByTagName("tbody")[0], o = 0; o < t.length; o++) {
        var i;
        (i = n.insertRow(o)).insertCell(0).innerHTML = t[o];
        var r = i.insertCell(1),
            c = t[o].replace(/\\/g, "\\\\");
        r.innerHTML = '<button class="btn btn-primary" onclick="viewImage(\'' + c + '\')"><i class="fas fa-image"></i> Ver Reporte</button>'
    }
})).catch((e => console.error(e)));