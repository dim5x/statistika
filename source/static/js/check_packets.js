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

    // function pack(data) {
    //     console.log('data', typeof(data['data']), data['data']);
    //     // Получаем список ссылок из переданных данных
    //     var linkList = data['data'].split(','); // Разбиваем список ссылок по запятым
    //
    //     // Находим div, в который мы хотим поместить список ссылок
    //     var divElement = document.getElementById('serverResponse'); // Замените 'yourDivId' на ID вашего div
    //
    //     // Очищаем содержимое div перед добавлением новых элементов
    //     divElement.innerHTML = '';
    //     divElement.innerHTML = linkList;
    //     // Для каждой ссылки создаем элемент <a> и добавляем его в div
    //     // linkList.forEach(function (link) {
    //     //     // var linkElement = document.createElement('a');
    //     //     // linkElement.href = link.trim(); // Убираем лишние пробелы
    //     //     // linkElement.textContent = link.trim(); // Устанавливаем текст ссылки
    //     //     divElement.appendChild(link); // Добавляем ссылку в div
    //     //     divElement.appendChild(document.createElement('br')); // Добавляем перенос строки
    //     // });
    // }

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
                d = document.getElementById('serverResponse');
                d.innerHTML =''
                d.innerHTML = data['data'].split('\n');
                // pack(data);
                // updateTableFromAjax();
            })
            .catch(error => {
                console.error('Fetch error:', error); // Обработка ошибок
            });
        // Здесь можно выполнить дополнительные действия с данными (например, отправка на сервер)
    });

});