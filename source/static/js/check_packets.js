$(document).ready(function () {
    // Добавление нового поля ввода при нажатии на кнопку
    let inputCount = 1;
    $('#add-input').click(function () {
        inputCount++;
        $('#input-container').append(
            '<div class="input-group">' +
            '<label for="game-name-' + inputCount + '">ID пакета: </label>' +
            '<input type="text" id="game-name-' + inputCount + '" name="game-name[]">' +
            '</div>'
        );
    });

    // Обработка отправки формы
    $('#game-form').submit(function (event) {
        event.preventDefault(); // Отмена стандартного действия отправки формы
        // Сбор значений всех полей ввода
        let gameNames = [];
        $('input[name="game-name[]"]').each(function () {
            gameNames.push($(this).val());
        });
        // Дальнейшие действия с данными (например, отправка на сервер)
        console.log(gameNames);

        fetch('/check_packet', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(gameNames)
        })
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('Network response was not ok.');
            })
            .then(data => {
                console.log(data); // Обработка успешного ответа от сервера
                let d = document.getElementById('serverResponse');
                d.innerHTML = data['data'].split('\n').join('<br>');
            })
            .catch(error => {
                console.error('Fetch error:', error); // Обработка ошибок
            });
        // Здесь можно выполнить дополнительные действия с данными (например, отправка на сервер)
    });
});