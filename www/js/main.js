var miners = [];
var dogs = [];


function showSuccess(text){
    var html =
        '<div class="alert alert-success">' +
            '<div class="alert-content-wrapper">' +
                text +
            '</div>' +
        '</div>';

    $('.alerts-wrapper').append(html);
}

function showSuccess(text){
    var html =
        '<div class="alert alert-error">' +
            '<div class="alert-content-wrapper">' +
                text +
            '</div>' +
        '</div>';
    $('.alerts-wrapper').append(html);
}

function cardTemplate(miner) {
    var html = '<div id="card' + miner.name + '" class="card miner-card">' +
        '<div class="card-area-main">' +
            '<div class="card-title-primary">' +
                '<div class="card-title-box">' +
                    '<div class="card-title-primary-text">' +
                        miner.name +
                    '</div>' +
                '<div class="card-subtitle-primary-text">' +
                    miner.ip +
                '</div>' +
            '</div>' +
        '</div>' +
        dogsSelectTemplate() +
    '</div>';

    return html;
}

function dogsSelectTemplate() {
    var html =
        '<div class="card-content">' +
            '<div class="select-box">' +
                '<select class="dog-select">' +
                    '<option selected disabled>' + 'Choose dog' + '</option>';

    $.each(dogs, function(index, dog) {
        html += '<option value="' + dog.localIP +'">' + dog.localIP + '</option>';
    });

    html += '</select></div></div>';
    return html;
}

function redrawMiner(miner) {
    if(miner.dog_id)
        return false;

    var isNewMiner = true;
    for(var i=0; i<miners.length; i++)
        if(miner.name == miners[i].name) {
            isNewMiner = false;
            break;
        }

    if(isNewMiner) {
        miners.push(miner);
        var html = cardTemplate(miner);
        $('.miner-wrapper').append(html);

        //Register new events for selects
        selectOnChangeListener();
    }
}

function redrawDogSelects(){
    $.each(miners, function(index, miner) {
        var card = $('#card' + miner.name);
        card.find('.card-content').remove();
        card.append(dogsSelectTemplate());
    });
}

function buttonTemplate(buttonText) {
    var html =
        '<div class="buttons-group-item">' +
            '<button class="button button-flat">' +
                '<div class="button-text">' + buttonText + '</div>' +
            '</button>' +
        '</div>';
    return html;
}

function buttonsGroupTemplate(buttonsTexts) {
    var html = '<td><div class="buttons-group">';
    for(var i=0; i<buttonsTexts.length; i++)
        html += buttonTemplate(buttonsTexts[i]);
    html += '</div></td>';
    return html;
}

function dogsTableHeadTemplate() {
    var html =
        '<thead><tr>' +
            '<td class="column-header">name</td>' +
            '<td class="column-header">IP</td>' +
            '<td class="column-header">dog port</td>' +
            '<td class="column-header">powered on</td>' +
            '<td class="column-header">last share</td>' +
            '<td class="column-header"></td>' +
        '</tr></thead>';
    return html;
}

function dogsTableRowTemplate(minerFromDogState) {
    var html =
        '<tr id="row' + minerFromDogState.name + '" </td>' +
            '<td class="name">' + minerFromDogState.name + '</td>' +
            '<td class="host">' + minerFromDogState.host + '</td>' +
            '<td class="port">' + minerFromDogState.mp710_port + '</td>' +
            '<td class="powered">' + minerFromDogState.last_power_on_date + '</td>' +
            '<td class="submitted">' + minerFromDogState.last_submitted_date + '</td>' +
            buttonsGroupTemplate(['unbind']) +
        '</tr>';
    return html;
}

function redrawTableRow(minerFromDogState) {
    var row = $('#row' + minerFromDogState.name);
    row.find('.name').html(minerFromDogState.name);
    row.find('.host').html(minerFromDogState.host);
    row.find('.port').html(minerFromDogState.mp710_port);
    row.find('.powered').html(minerFromDogState.last_power_on_date);
    row.find('.submitted').html(minerFromDogState.last_submitted_date);
}

function drawDogsWrapper() {
    var html =
        '<div class="tables-list">' +
			'<div class="centering-wrapper">' +
            '</div>' +
        '</div>';

    $('.body-wrapper').append(html);
}

function drawDogsTables() {

    for(var i=0; i<dogs.length; i++) {

        var html = '';
        var table = $('#dog' + i);
        if(!table.length)
            html +=
                '<div id="dog' + i + '" class="dog-table-wrapper">' +
                    '<div class="dog-table-title">' +
                        dogs[i].localIP +
                    '</div>' +
                    '<table class="data-table">' +
                        dogsTableHeadTemplate() +
                        '<tbody>';

        $.each(dogs[i].miners, function(index, miner) {
            var row = $('#row' + miner.name);

            if (row.length)
                redrawTableRow(miner);
            else
                html += dogsTableRowTemplate(miner);
        });


        if (!table.length) {
            html += '</tbody></table></div>';
            $('.centering-wrapper').append(html);
        }
        else
            table.find('tbody').append(html);
    }

}

function removeAbsentMiners(actualMiners) {

}

function findMiner(minerName){
    for(var i=0; i<miners.length; i++)
        if(miners[i].name == minerName)
            return miners[i];
    return false
}

function bindMiner(minerName, dogIP){
    $.ajax({url: "/bind?name=" + minerName + "&dogIP=" + dogIP, method: "GET"})
        .done(function(){
            $('#card' + minerName).remove();
            showSuccess();
        })
        .fail(function(){showError();});
}

function selectOnChangeListener(){
    $('.dog-select').change(function(){
        bindMiner(
            $(this).closest('.miner-card').find('.card-title-primary-text').html(),
            $(this).val()
        );
    });
}

$(document).ready(function() {

    drawDogsWrapper();

    (function get_miners() {
        setTimeout(function()
        {
            $.ajax({url: "/miners", method: "GET"})
                .done(function(data) {
                    var actualMiners = JSON.parse(data).miners;
                    $.each(actualMiners, function(index, miner) {
                        redrawMiner(miner);
                    });
                })
                .always(get_miners());
        }, 1000);
    })();

    (function get_dogs() {
        setTimeout(function() {
            $.ajax({url: "/dogs", method: "GET"})
                .done(function(data) {
                    var actualDogs = JSON.parse(data).dogs;

                    if(actualDogs.length != dogs.length) {
                        dogs = actualDogs;
                        redrawDogSelects();

                        //Register new events for selects
                        selectOnChangeListener();
                        drawDogsTables();
                    }
                    else {
                        dogs = actualDogs;
                        drawDogsTables();
                    }
                })
                .always(get_dogs());
        }, 1000);
    })();
});
