numlines=student_code.split(/\r\n|\r|\n/).length

// Generate contents

// Ace editor:
var editor = ace.edit("editor", {
    maxLines:numlines,
    minLines:numlines
});
editor.setTheme("ace/theme/dawn");
editor.session.setMode("ace/mode/python");
editor.setValue(student_code)
editor.clearSelection()
editor.focus();


// diff:
if(show_diff) {
    console.log('test')
    var diff = Diff.createTwoFilesPatch("student", "correct", student_code, correct_code,null,null,{context:100});
    console.log(diff)
    var diffHtml = Diff2Html.html(diff, {
        drawFileList: false,
        // matching: 'words', // a more fine-grained option for displaying the diff
        outputFormat: 'side-by-side',
        renderNothingWhenEmpty: false,
    });
    document.getElementById('diff').innerHTML = diffHtml;
// inject headers:
    document.getElementsByClassName('d2h-file-side-diff')[0].insertAdjacentHTML('afterbegin',
        '<div style="padding:5px;font-weight:bold;text-decoration:underline;"> Student code </div>')
    document.getElementsByClassName('d2h-file-side-diff')[1].insertAdjacentHTML('afterbegin',
        '<div style="padding:5px;font-weight:bold;text-decoration:underline;">  Generated correction </div>')
}

// not diff (student code only):
if(!show_diff) {
    console.log('control')
    var scode = ace.edit("studentcode", {
        maxLines: numlines,
        minLines: numlines
    });
    scode.setTheme("ace/theme/github");
    scode.session.setMode("ace/mode/python");
    scode.setValue(student_code)
    scode.clearSelection()
    scode.setOptions({readOnly: true, highlightActiveLine: false, highlightGutterLine: false});
    scode.renderer.$cursorLayer.element.style.display = "none"
}

// Set up unit test interface:
function gen_unit_tests(){
    for(t of problem_data.test_case_data_list) {
        $('#unit_tests').append(`
        <tr>
            <td><pre>${problem_name}(${t.input})</pre></td>
            <td>${t.output}</td>
            <td id="${t.test_case_name}"></td>
        </tr>
        `)
    }
}
gen_unit_tests()


// At the beginning, the unit tests are most certainly not correct
$("#is_correct")[0].setCustomValidity('Please make sure that all unit tests pass');


// run unit tests (when requested):
function run_unit_tests() {
    const prog = editor.getValue();
    $('#code_contents').val(prog)
    const test_strings = problem_data.test_case_data_list.map( (t) => `${problem_name}(${t.input})`)
    const test_expected = problem_data.test_case_data_list.map( (t) => t.output)

    console.log(test_strings)

    $.ajax({
        type: 'POST',
        url: "/run_code",
        data: {
            code: prog,
            test_strings: JSON.stringify(test_strings),
            test_expected: JSON.stringify(test_expected)
        },
        dataType: "text",
        success: function(data){
            console.log(JSON.parse(data))
            output = JSON.parse(data)
            correct = true
            for(let i=0; i<problem_data.test_case_data_list.length; i++) {
                const t = problem_data.test_case_data_list[i]
                $(`#${t.test_case_name}`).text(output.output[i])
                if (output.correct[i]) {
                    $(`#${t.test_case_name}`).css('background-color', '#ddffdd');
                }
                else {
                    $(`#${t.test_case_name}`).css('background-color', '#fee8ea');
                    correct=false
                }
            }
            if(correct || seconds_left <= 0){
                    $("#is_correct").val(true);
                    $("#is_correct")[0].setCustomValidity('');
                    console.log('correct')

            }
            else {
                    $("#is_correct").val(false);
                    $("#is_correct")[0].setCustomValidity('Please make sure that all unit tests pass');
                    console.log('wrong')
            }
        }
    });
 }

let seconds_left = 8*60
let timer_interval = setInterval(function() {
    seconds_left -= 1
    $('#timer').text(Math.floor(seconds_left/60)+':' + (seconds_left%60).toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping:false}))

    if(seconds_left <= 60) {
        $('#timer').css('color', 'red')
    }

    if(seconds_left <= 0) {
        clearInterval(timer_interval);
        $("#is_correct")[0].setCustomValidity('');
        $('#warning').css('display', 'block')
    }
 }, 1000)
