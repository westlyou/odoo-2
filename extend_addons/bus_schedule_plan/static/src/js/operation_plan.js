odoo.define('operate_plan_conf', function (require) {
    "use strict";
    var Model = require('web.Model');
    var model = new Model("scheduleplan.busmovetime");

    function checkTime(i) {
        if (i < 10) {
            i = "0" + i;
        }
        return i;
    }

    function render_plan(data) {
        $('.up_carNum').html(data.upvehicle);
        $('.up_station_info').html(data.upstation + "-" + data.downstation)
        if (data.directiontype != 'singleway') {
            $('.down_carNum').html(data.downvehicle);
            $('.down_station_info').html(data.downstation + "-" + data.upstation);
        } else {
            $('.dbl_state').hide();
        }
        var bus_num = Object.keys(data.bus).length;
        //渲染table
        if (data.direction.down.length != 0 && data.direction.up.length != 0) {
            for (var ts = 0; ts < data.bus[1].length; ts++) {
                if (ts % 2 == 0) {
                    $('.time_start_arrive_stop thead tr').append('<th><div>' + ts + '</div><div>' + data.upstation.substr(0, 1) + '-' + data.downstation.substr(0, 1) + '</div></th>')
                } else {
                    $('.time_start_arrive_stop thead tr').append('<th><div>' + ts + '</div><div>' + data.downstation.substr(0, 1) + '-' + data.upstation.substr(0, 1) + '</div></th>')
                }
            }
        } else {
            for (var ts = 0; ts < data.bus[1].length; ts++) {
                $('.time_start_arrive_stop thead tr').append('<th><div>' + ts + '</div><div>' + data.upstation.substr(0, 1) + '-' + data.upstation.substr(0, 1) + '</div></th>');
            }
        }
        for (var bn = 1; bn < (bus_num + 1); bn++) {
            $('.time_start_arrive_stop tbody').append('<tr><td>' + bn + '</td></tr>');
            for (var bTdo = 0; bTdo < $('.time_start_arrive_stop thead tr th').length - 1; bTdo++) {
                $('.time_start_arrive_stop').find('tr').eq(bn).append('<td>' + $('.start_over_stop_time').html() + '</td>');
            }
            for (var bTd = 0; bTd < data.bus[bn].length; bTd++) {
                //没有排班的
                if (data.bus[bn][bTd] != null) {
                    // 排班被换掉的
                    if (data.bus[bn][bTd][1][1] != null) {
                        var timesHours = checkTime(new Date(data.bus[bn][bTd][1][1].startmovetime).getHours());
                        var timesMin = checkTime(new Date(data.bus[bn][bTd][1][1].startmovetime).getMinutes());
                        var timeaHours = checkTime(new Date(data.bus[bn][bTd][1][1].arrive_time).getHours());
                        var timeaMin = checkTime(new Date(data.bus[bn][bTd][1][1].arrive_time).getMinutes());
                        $('.time_start_arrive_stop').find('tr').eq(bn).find('td').eq(bTd + 1).attr('direction', data.bus[bn][bTd][1][1].direction).attr('index', data.bus[bn][bTd][0]);
                        $('.time_start_arrive_stop').find('tr').eq(bn).find('td').eq(bTd + 1).find('.start_time').html('<span>发</span><span class="time_left">' + timesHours + ':' + timesMin + '</span>');
                        $('.time_start_arrive_stop').find('tr').eq(bn).find('td').eq(bTd + 1).find('.over_time').html('<span>达</span><span class="time_left">' + timeaHours + ':' + timeaMin + '</span>');
                        if (data.bus[bn][bTd][4] != undefined) {
                            $('.time_start_arrive_stop').find('tr').eq(bn).find('td').eq(bTd + 1).find('.stop_time').html('<span>停</span><span class="time_left">' + data.bus[bn][bTd][4] + '</span>');
                        }
                    } else {
                        $('.time_start_arrive_stop').find('tr').eq(bn).find('td').eq(bTd + 1).attr('direction', data.bus[bn][bTd][2]).attr('index', data.bus[bn][bTd][0]).addClass('sort_out').html($('.start_over_stop_time').html());
                    }
                } else {
                    $('.time_start_arrive_stop').find('tr').eq(bn).find('td').eq(bTd + 1).addClass("not_click").css({
                        'cursor': 'not-allowed'
                    });
                }
            }
        }
        if (sessionStorage.getItem('direction')) {
            sessionStorage.removeItem('direction');
        }
        sessionStorage.setItem('direction', JSON.stringify(data.direction));
    }

    // window.onhashchange = function () {


    window.onhashchange = function () {
        var set_time = setInterval(function () {
            if ($('body').find('.plan_operate_config').length > 0) {
                clearInterval(set_time)
                var recid = $('#the_rec_id .o_form_field').text();
                console.log(recid)
                model.call("reoppaln2web", [recid]).then(function (data) {
                    $('.time_start_arrive_stop').html('<thead><tr><th>班次</th></tr></thead><tbody></tbody>');
                    render_plan(data);
                });
                $('.time_start_arrive_stop').on('dblclick', 'tbody td:not(.not_click)', function () {
                    // 不是空的
                    // 点击的index
                    var this_index = $(this).attr("index");
                    //点击的direction
                    var direction = $(this).attr('direction');
                    // direction缓存对象
                    var directionObj = JSON.parse(sessionStorage.getItem('direction'));
                    sessionStorage.removeItem('direction');
                    // 点击有计划的为0,否则为1
                    var click_td = 0;
                    if ($(this).hasClass('sort_out')) {
                        click_td = 1;
                    } else {
                        click_td = 0;
                    }
                    model.call("changeOpplan", [recid, this_index, direction, directionObj, click_td]).then(function (res) {
                        $('.time_start_arrive_stop').html('<thead><tr><th>班次</th></tr></thead><tbody></tbody>');
                        render_plan(res);
                    });
                });
                $('.save_plan.btn').click(function () {
                    var directionObj = JSON.parse(sessionStorage.getItem('direction'));
                    model.call("saveOpPlan", [recid, directionObj]).then(function (res) {
                    });
                });
                $('.giveup_plan').click(function () {
                    model.call("reoppaln2web", [recid]).then(function (data) {
                        $('.time_start_arrive_stop').html('<thead><tr><th>班次</th></tr></thead><tbody></tbody>');
                        render_plan(data);
                    });
                });
            }
        }, 300)

    }

    // };
});
