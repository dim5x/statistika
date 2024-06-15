let modal = document.getElementById("myModal");
let btn = document.getElementById("set_result_button");
let sendBtn = document.getElementById("send-result");
let span = document.getElementsByClassName("close")[0];
let teamNames; // Переменная для хранения списка имен команд

btn.onclick = function () {
    // Очистить существующие элементы
    document.getElementById("team-list").innerHTML = "";

    // Получить названия команд на основе атрибута 'tabulator-field="team_name"' и исключить первый элемент
    teamNames = Array.from(document.querySelectorAll("[tabulator-field='team_name']")).map(function (team) {
        return team.textContent;
    }).slice(1); // Исключаем первый элемент из массива

    teamNames.forEach(function (name) {
        let div = document.createElement("div");

        let label = document.createElement("label");
        label.textContent = name;
        label.setAttribute("for", "result-" + name);
        label.setAttribute("class", "modal_label")

        label.style.marginRight = "10px"; // Добавляем отступ между лейблом и полем ввода

        let input = document.createElement("input");
        input.setAttribute("type", "text");
        input.setAttribute("id", "result-" + name);
        input.setAttribute("class", "modal_input")
        input.setAttribute("autocomplete", "off")
        input.setAttribute("name", "result-" + name);
        // input.setAttribute('autofocus', 'autofocus');
        // input.setAttribute("value", "0")

        div.appendChild(label);
        div.appendChild(input);

        document.getElementById("team-list").appendChild(div);
    });

    modal.style.display = "block";
}

sendBtn.onclick = function () {
    let data = {};
    teamNames.forEach(function (name) {
        let input = document.getElementById("result-" + name);
        data[name] = input.value;
    });

    fetch('/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            // Дополнительные действия при успешной отправке данных
        })
        .catch((error) => {
            console.error('Error:', error);
            // Обработка ошибки при отправке данных
        });

    modal.style.display = "none"; // Закрыть модальное окно после отправки данных
}

span.onclick = function () {
    modal.style.display = "none";
}

window.onclick = function (event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}