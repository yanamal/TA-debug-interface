import csv
import glob
import json
import multiprocessing
import random
from flask import Flask, render_template, request, redirect, url_for
import logging

import astor as astor
import ast


logging.basicConfig(filename='applog.txt', format='%(asctime)s,%(name)s,%(levelname)s,%(message)s', level=logging.INFO)
app = Flask(__name__)
with open('data/problems.json') as f:
    app.problems = json.load(f)
solution_files = glob.glob('data/solutions_study.csv')
app.solutions = []


# Shuffle solutions for Experiment 1: present problems from each condition all in a row; shuffle condition order
def shuffle_solutions_stage1(sol_opts):
    control = []
    exp = []

    random.shuffle(sol_opts['large'])
    random.shuffle(sol_opts['small'])

    for issue in ['large', 'small']:
        for i in range(len(sol_opts[issue]) // 2):
            control.append(sol_opts[issue].pop())
            exp.append(sol_opts[issue].pop())

    random.shuffle(control)
    random.shuffle(exp)

    for c_prob in control:
        c_prob['control'] = 'true'

    for e_prob in exp:
        e_prob['control'] = 'false'

    if random.random() < 0.5:
        app.solutions.extend(control)
        app.solutions.extend(exp)
    else:
        app.solutions.extend(exp)
        app.solutions.extend(control)


# Shuffle solutions for Experiment 2: control and experiment problems all mixed together;
# Also, in experiment, substitute in "problematic" solution
def shuffle_solutions_stage2(sol_opts):
    random.shuffle(sol_opts['large'])
    random.shuffle(sol_opts['small'])

    problems = []

    # get "control" problems
    for issue in ['large', 'small']:
        for i in range(len(sol_opts[issue]) // 2):
            next_prob = sol_opts[issue].pop()
            next_prob['control'] = 'true'
            problems.append(next_prob)

    # get "test" problems
    for issue in ['large', 'small']:
        for i in range(len(sol_opts[issue])):
            next_prob = sol_opts[issue].pop()
            next_prob['control'] = 'false'
            next_prob['solution'] = next_prob['bad_solution']
            problems.append(next_prob)

    random.shuffle(problems)
    app.solutions = problems


# option for presenting problems in consistent order (for debugging)
def dont_shuffle(sol_opts):
    problems = []
    for issue in ['large', 'small']:
        for i in range(len(sol_opts[issue])):
            next_prob = sol_opts[issue].pop()
            next_prob['control'] = 'false'
            problems.append(next_prob)
    app.solutions = problems


solution_options = {
    'large': [],
    'small': []
}

for s in solution_files:
    with open(s, 'r') as csv_f:
        reader = csv.DictReader(csv_f)
        for row in reader:
            issue_type = row['issue']
            solution_options[issue_type].append(row)

# Change the following two lines to switch between types of experiment
shuffle_solutions_stage2(solution_options)
show_diff_in_control = True

solution_i = 0


def test_potential_timeout(code_string, unit_test_string):
    try:
        exec(code_string, globals())
        return eval(unit_test_string)
    except Exception as e:
        return str(e)


def run_unit_test(code_string, unit_test_string):
    with multiprocessing.Pool(processes=2) as pool:
        result = pool.apply_async(test_potential_timeout, (code_string, unit_test_string,))
        try:
            return result.get(timeout=0.1)
        except multiprocessing.TimeoutError:
            print('timeout')
            return 'Timeout(infinite loop?)'


@app.route('/')
def index():
    # reset index
    global solution_i
    solution_i = 0

    # parameters for redirecting to pre-survey (e.g. on Qualtrics)
    # which can then, in turn, redirect to the problem page when pre-survey is completed
    params = {
        'return': request.base_url + 'problem'
    }

    # Redirect to pre-survey here, if needed
    return redirect(url_for('show_problem'),
                    code=302)


@app.route('/post', methods=['GET', 'POST'])
def post_survey():
    return render_template('post.html')


@app.route('/problem', methods=['GET', 'POST'])
def show_problem():
    global solution_i
    if request.method == 'POST':
        solution_i += 1
        app.logger.info(f'problem_response,'
                        f'{request.values.get("code_state_id")},'
                        f'"{request.values.get("code_contents")}",'
                        f'"{request.values.get("explanation")}",'
                        f'"{request.values.get("review")}",'
                        )

    # TODO(P2): have output area (for print debugging)

    # if app.solutions is empty (and current solution is also solved), redirect to post-survey

    if len(app.solutions) == solution_i:
        # Redirect to a post-survey here
        return "All problems completed, thank you!"

    solution = app.solutions[solution_i]  # app.solutions has been shuffled

    p_name = solution['problem']
    p_data = app.problems['unit_tests'][p_name]

    # Log which problem was given

    # TODO: escape quotations by doubling them up(or actually put through csv encoder)
    #  (relevant when participant uses quotes in their free-text response)

    app.logger.info(f'problem,{solution["CodeStateID"]},{solution["control"]}')

    should_show_diff = 'true' if (show_diff_in_control or (solution['control'] == 'false')) else 'false'

    return render_template('problem.html',
                           student_code=astor.to_source(ast.parse(solution['code'])),
                           correct_code=astor.to_source(ast.parse(solution['solution'])),
                           problem_name=p_name,
                           problem_data=json.dumps(p_data),
                           problem_desc=p_data['problem_data']['description'],
                           control=solution['control'],
                           show_diff=should_show_diff,
                           CodeStateID=solution['CodeStateID'],
                           problem_i=solution_i
                           )


@app.route('/advance', methods=['GET', 'POST'])
def advance_solution_i():
    global solution_i
    if request.method == 'POST':
        solution_i = int(request.values.get("which"))

    return render_template('advance.html')


@app.route('/run_code', methods=['POST'])
def run_code():
    # app.logger.info(app.problems)
    code = request.form.get("code")
    test_strings = json.loads(request.form.get("test_strings"))
    test_expected = json.loads(request.form.get("test_expected"))
    test_output = [run_unit_test(code, test) for test in test_strings]

    app.logger.info(f'run_test,'
                    f'"{code}",'
                    f'"{test_expected}",'
                    f'"{[str(o) for o in test_output]}",'
                    )

    return json.dumps({
        'output': [str(o) for o in test_output],
        # TODO(P2 - not handling any floating-point right now):
        #  special handling of floating-point (precision gets in the way)
        'correct': [out == eval(exp) for (out, exp) in zip(test_output, test_expected)]
    })


if __name__ == '__main__':
    app.debug = True
    app.run(debug=True)

