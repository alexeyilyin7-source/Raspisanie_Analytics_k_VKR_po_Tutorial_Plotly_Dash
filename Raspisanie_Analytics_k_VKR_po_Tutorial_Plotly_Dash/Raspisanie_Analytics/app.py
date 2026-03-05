# app.py
import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Импорт модулей
from modules.data_loader import loader
from modules.optimization import optimization_engine
from modules.database import db_manager
from modules.schedule_validator import ScheduleValidator

# Инициализация приложения
external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap",
        "rel": "stylesheet",
    },
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True  # ВАЖНО: подавляем ошибки о ненайденных ID
server = app.server
app.title = "АИС Расписание ГУУ"

# Получение данных
data = loader.schedule_data
teachers = loader.teachers_data
groups = loader.groups_data
classrooms = loader.classrooms_data

# Инициализация БД
db_manager.init_database()
db_manager.import_from_csv(loader)

# --- МАКЕТ ПРИЛОЖЕНИЯ ---
app.layout = html.Div([
    # Шапка
    html.Div(
        children=[
            html.Div(
                children=[
                    html.Img(src="/assets/logo.png", className="header-logo"),
                    html.H1("Автоматизированная информационная система расписания (АИСР)",
                            className="header-title"),
                    html.P("Государственный Университет Управления",
                           className="header-subtitle"),
                ],
                className="header-content"
            ),
        ],
        className="header"
    ),

    # Панель навигации
    html.Div(
        children=[
            dcc.Tabs(id="tabs", value="tab-dashboard", children=[
                dcc.Tab(label="📊 Дашборд", value="tab-dashboard"),
                dcc.Tab(label="📅 Расписание", value="tab-schedule"),
                dcc.Tab(label="⚙️ Оптимизация", value="tab-optimization"),
                dcc.Tab(label="👥 Преподаватели", value="tab-teachers"),
                dcc.Tab(label="🏛 Аудитории", value="tab-classrooms"),
                dcc.Tab(label="📈 Аналитика", value="tab-analytics"),
            ]),
        ],
        className="tabs-container"
    ),

    # Основной контент (будет заполняться колбэком)
    html.Div(id="tab-content", className="content"),

    # Footer
    html.Div(
        children=[
            html.P("© 2026 Государственный Университет Управления. Все права защищены."),
            html.P("Версия 1.0.0 | Разработано в рамках дипломного проекта"),
        ],
        className="footer"
    )
])


# --- КОЛЛБЭК ДЛЯ ПЕРЕКЛЮЧЕНИЯ ВКЛАДОК ---
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "value")
)
def render_content(tab):
    if tab == "tab-dashboard":
        return render_dashboard()
    elif tab == "tab-schedule":
        return render_schedule()
    elif tab == "tab-optimization":
        return render_optimization()
    elif tab == "tab-teachers":
        return render_teachers()
    elif tab == "tab-classrooms":
        return render_classrooms()
    elif tab == "tab-analytics":
        return render_analytics()
    return html.Div()


# --- ФУНКЦИИ ОТОБРАЖЕНИЯ ВКЛАДОК ---

def render_dashboard():
    """Рендеринг дашборда"""
    institutes = data['institute'].unique() if not data.empty else []
    lesson_types = data['lesson_type'].unique() if not data.empty else []

    return html.Div([
        html.H2("Панель управления расписанием"),

        # Фильтры
        html.Div([
            html.Div([
                html.Label("Институт:"),
                dcc.Dropdown(
                    id="dashboard-institute",
                    options=[{"label": "Все", "value": "Все"}] +
                            [{"label": i, "value": i} for i in institutes],
                    value="Все"
                )
            ], className="filter-item"),

            html.Div([
                html.Label("Тип занятия:"),
                dcc.Dropdown(
                    id="dashboard-lesson-type",
                    options=[{"label": "Все", "value": "Все"}] +
                            [{"label": lt, "value": lt} for lt in lesson_types],
                    value="Все"
                )
            ], className="filter-item"),

            html.Div([
                html.Label("Дата начала:"),
                dcc.DatePickerSingle(
                    id="dashboard-start-date",
                    date=data['date'].min() if not data.empty else None
                )
            ], className="filter-item"),

            html.Div([
                html.Label("Дата окончания:"),
                dcc.DatePickerSingle(
                    id="dashboard-end-date",
                    date=data['date'].max() if not data.empty else None
                )
            ], className="filter-item"),
        ], className="filters-row"),

        # Карточки с метриками
        html.Div([
            html.Div([
                html.H3("Всего занятий"),
                html.P(id="total-classes", children="0", className="metric-value"),
                html.P("за период", className="metric-label")
            ], className="metric-card"),

            html.Div([
                html.H3("Средняя нагрузка"),
                html.P(id="avg-load", children="0", className="metric-value"),
                html.P("часов", className="metric-label")
            ], className="metric-card"),

            html.Div([
                html.H3("Преподавателей"),
                html.P(id="total-teachers", children="0", className="metric-value"),
                html.P("активных", className="metric-label")
            ], className="metric-card"),

            html.Div([
                html.H3("Групп"),
                html.P(id="total-groups", children="0", className="metric-value"),
                html.P("всего", className="metric-label")
            ], className="metric-card"),
        ], className="metrics-row"),

        # Графики
        html.Div([
            html.Div([
                dcc.Graph(id="load-by-institute")
            ], className="chart-card"),

            html.Div([
                dcc.Graph(id="load-by-date")
            ], className="chart-card"),
        ], className="charts-row"),

        html.Div([
            html.Div([
                dcc.Graph(id="classes-by-type")
            ], className="chart-card"),

            html.Div([
                dcc.Graph(id="teacher-workload")
            ], className="chart-card"),
        ], className="charts-row"),
    ])


def render_schedule():
    """Рендеринг страницы расписания"""
    group_options = []
    if groups is not None and not groups.empty:
        group_options = [{"label": g, "value": g} for g in groups['group_name'].unique()]

    teacher_options = []
    if teachers is not None and not teachers.empty:
        teacher_options = [{"label": t, "value": t} for t in teachers['full_name'].unique()]

    return html.Div([
        html.H2("Расписание занятий"),

        html.Div([
            html.Div([
                html.Label("Группа:"),
                dcc.Dropdown(
                    id="schedule-group",
                    options=group_options,
                    placeholder="Выберите группу"
                )
            ], className="filter-item"),

            html.Div([
                html.Label("Преподаватель:"),
                dcc.Dropdown(
                    id="schedule-teacher",
                    options=teacher_options,
                    placeholder="Выберите преподавателя"
                )
            ], className="filter-item"),

            html.Div([
                html.Label("Неделя:"),
                dcc.Dropdown(
                    id="schedule-week",
                    options=[
                        {"label": "Четная", "value": "even"},
                        {"label": "Нечетная", "value": "odd"},
                        {"label": "Обе", "value": "both"}
                    ],
                    value="both"
                )
            ], className="filter-item"),

            html.Div([
                html.Button("Применить фильтры", id="apply-schedule-filters",
                            className="primary-button"),
                html.Button("Экспорт в Excel", id="export-schedule",
                            className="secondary-button"),
            ], className="filter-item"),
        ], className="filters-row"),

        html.Div([
            html.Div([
                html.H3("Календарь занятий"),
                dcc.Graph(id="schedule-calendar")
            ], className="chart-card"),

            html.Div([
                html.H3("Таблица расписания"),
                dash_table.DataTable(
                    id="schedule-table",
                    columns=[
                        {"name": "Дата", "id": "date"},
                        {"name": "Время", "id": "time"},
                        {"name": "Дисциплина", "id": "discipline"},
                        {"name": "Преподаватель", "id": "teacher_name"},
                        {"name": "Группа", "id": "group_name"},
                        {"name": "Аудитория", "id": "room"},
                        {"name": "Тип", "id": "lesson_type"},
                    ],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '10px'},
                    style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                    page_size=10
                )
            ], className="chart-card"),
        ], className="charts-row"),
    ])


def render_optimization():
    """Рендеринг страницы оптимизации"""
    return html.Div([
        html.H2("Оптимизация расписания"),

        html.Div([
            html.Div([
                html.H3("Параметры оптимизации"),

                html.Label("Алгоритм:"),
                dcc.Dropdown(
                    id="opt-algorithm",
                    options=[
                        {"label": "Генетический алгоритм (ГА)", "value": "ga"},
                        {"label": "Имитация отжига (SA)", "value": "sa"},
                        {"label": "Жадный алгоритм", "value": "greedy"},
                        {"label": "Комбинированный (рекомендуется)", "value": "auto"}
                    ],
                    value="auto"
                ),

                html.Label("Размер популяции (для ГА):", style={"marginTop": "15px"}),
                dcc.Slider(
                    id="ga-population",
                    min=10, max=100, step=10, value=30,
                    marks={10: '10', 30: '30', 50: '50', 100: '100'}
                ),

                html.Label("Количество поколений:", style={"marginTop": "15px"}),
                dcc.Slider(
                    id="ga-generations",
                    min=10, max=200, step=10, value=50,
                    marks={10: '10', 50: '50', 100: '100', 200: '200'}
                ),

                html.Label("Начальная температура (для SA):", style={"marginTop": "15px"}),
                dcc.Slider(
                    id="sa-temperature",
                    min=10, max=200, step=10, value=100,
                    marks={10: '10', 50: '50', 100: '100', 200: '200'}
                ),

                html.Button("Запустить оптимизацию", id="run-optimization",
                            className="primary-button", style={"marginTop": "20px", "width": "100%"}),
            ], className="optimization-params"),

            html.Div([
                html.H3("Результаты оптимизации"),
                html.Div(id="optimization-results", children="Нажмите 'Запустить оптимизацию' для начала",
                         className="results-box"),

                html.H4("График сходимости", style={"marginTop": "20px"}),
                dcc.Graph(id="convergence-graph"),

                html.H4("Сравнение алгоритмов", style={"marginTop": "20px"}),
                dcc.Graph(id="algorithms-comparison"),
            ], className="optimization-results"),
        ], className="optimization-container"),
    ])


def render_teachers():
    """Рендеринг страницы преподавателей"""
    teacher_data = teachers.to_dict('records') if teachers is not None and not teachers.empty else []

    return html.Div([
        html.H2("Управление преподавателями"),

        html.Div([
            html.Button("Добавить преподавателя", id="add-teacher",
                        className="primary-button"),
            html.Button("Импорт из Excel", id="import-teachers",
                        className="secondary-button"),
        ], style={"marginBottom": "20px"}),

        dash_table.DataTable(
            id="teachers-table",
            columns=[
                {"name": "ID", "id": "teacher_id"},
                {"name": "ФИО", "id": "full_name"},
                {"name": "Кафедра", "id": "department"},
                {"name": "Макс. часов/день", "id": "max_hours_per_day"},
                {"name": "Email", "id": "email"},
                {"name": "Телефон", "id": "phone"},
            ],
            data=teacher_data,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
            page_size=15,
            editable=True
        ),
    ])


def render_classrooms():
    """Рендеринг страницы аудиторий"""
    classroom_data = classrooms.to_dict('records') if classrooms is not None and not classrooms.empty else []

    # Статистика
    total_rooms = len(classrooms) if classrooms is not None else 0
    lecture_rooms = len(
        classrooms[classrooms['room_type'] == 'ЛК']) if classrooms is not None and not classrooms.empty else 0
    computer_rooms = len(
        classrooms[classrooms['room_type'] == 'ЦИТ']) if classrooms is not None and not classrooms.empty else 0
    total_capacity = classrooms['capacity'].sum() if classrooms is not None and not classrooms.empty else 0

    return html.Div([
        html.H2("Управление аудиториями"),

        # Карточки статистики
        html.Div([
            html.Div([
                html.H3("Всего аудиторий"),
                html.P(total_rooms, className="metric-value"),
            ], className="metric-card-small"),

            html.Div([
                html.H3("Лекционных"),
                html.P(lecture_rooms, className="metric-value"),
            ], className="metric-card-small"),

            html.Div([
                html.H3("Компьютерных"),
                html.P(computer_rooms, className="metric-value"),
            ], className="metric-card-small"),

            html.Div([
                html.H3("Общая вместимость"),
                html.P(total_capacity, className="metric-value"),
            ], className="metric-card-small"),
        ], className="metrics-row-small"),

        # Карта загруженности
        html.Div([
            dcc.Graph(id="classroom-occupancy")
        ], className="chart-card"),

        # Таблица аудиторий
        html.Div([
            dash_table.DataTable(
                id="classrooms-table",
                columns=[
                    {"name": "ID", "id": "room_id"},
                    {"name": "Корпус", "id": "building"},
                    {"name": "Номер", "id": "room_number"},
                    {"name": "Вместимость", "id": "capacity"},
                    {"name": "Тип", "id": "room_type"},
                    {"name": "Оборудование", "id": "equipment"},
                ],
                data=classroom_data,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '10px'},
                style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                page_size=10
            )
        ], className="chart-card", style={"marginTop": "20px"}),
    ])


def render_analytics():
    """Рендеринг страницы аналитики"""
    return html.Div([
        html.H2("Аналитика и отчеты"),

        html.Div([
            html.Div([
                html.Label("Тип отчета:"),
                dcc.Dropdown(
                    id="report-type",
                    options=[
                        {"label": "Нагрузка преподавателей", "value": "teacher_load"},
                        {"label": "Загруженность аудиторий", "value": "room_usage"},
                        {"label": "Успеваемость групп", "value": "group_progress"},
                        {"label": "Распределение по типам занятий", "value": "lesson_distribution"}
                    ],
                    value="teacher_load"
                )
            ], className="filter-item", style={"width": "300px"}),

            html.Div([
                html.Label("Период:"),
                dcc.Dropdown(
                    id="report-period",
                    options=[
                        {"label": "Текущий семестр", "value": "current"},
                        {"label": "Прошлый семестр", "value": "previous"},
                        {"label": "Учебный год", "value": "year"},
                        {"label": "Весь период", "value": "all"}
                    ],
                    value="current"
                )
            ], className="filter-item", style={"width": "200px"}),

            html.Button("Сформировать отчет", id="generate-report",
                        className="primary-button"),
        ], className="filters-row"),

        html.Div([
            html.Div([
                dcc.Graph(id="report-chart-1")
            ], className="chart-card"),

            html.Div([
                dcc.Graph(id="report-chart-2")
            ], className="chart-card"),
        ], className="charts-row"),

        html.Div([
            html.H3("Детализированный отчет"),
            html.Div(id="report-details", className="report-details"),
            html.Button("Экспорт в PDF", id="export-pdf",
                        className="secondary-button", style={"marginTop": "10px"}),
        ], className="chart-card"),
    ])


# --- КОЛЛБЭКИ ДЛЯ ДАШБОРДА ---
@app.callback(
    [Output("total-classes", "children"),
     Output("avg-load", "children"),
     Output("total-teachers", "children"),
     Output("total-groups", "children"),
     Output("load-by-institute", "figure"),
     Output("load-by-date", "figure"),
     Output("classes-by-type", "figure"),
     Output("teacher-workload", "figure")],
    [Input("dashboard-institute", "value"),
     Input("dashboard-lesson-type", "value"),
     Input("dashboard-start-date", "date"),
     Input("dashboard-end-date", "date")]
)
def update_dashboard(institute, lesson_type, start_date, end_date):
    """Обновление дашборда"""
    filtered_data = loader.get_filtered_data(
        institute=None if institute == "Все" else institute,
        lesson_type=None if lesson_type == "Все" else lesson_type,
        start_date=start_date,
        end_date=end_date
    )

    # Метрики
    total_classes = len(filtered_data)
    avg_load = round(filtered_data['teacher_load'].mean(), 2) if total_classes > 0 else 0
    total_teachers = filtered_data['teacher_name'].nunique() if total_classes > 0 else 0
    total_groups = filtered_data['group_name'].nunique() if total_classes > 0 else 0

    # График нагрузки по институтам
    if total_classes > 0:
        inst_load = filtered_data.groupby('institute')['teacher_load'].sum().reset_index()
        fig_institute = px.bar(inst_load, x='institute', y='teacher_load',
                               title='Суммарная нагрузка по институтам',
                               labels={'teacher_load': 'Нагрузка (часы)', 'institute': 'Институт'})
    else:
        fig_institute = px.bar(title='Нет данных')

    # График нагрузки по датам
    if total_classes > 0:
        date_load = filtered_data.groupby('date')['teacher_load'].sum().reset_index()
        fig_date = px.line(date_load, x='date', y='teacher_load',
                           title='Динамика нагрузки по датам',
                           labels={'teacher_load': 'Нагрузка (часы)', 'date': 'Дата'})
    else:
        fig_date = px.line(title='Нет данных')

    # График распределения по типам занятий
    if total_classes > 0:
        type_dist = filtered_data['lesson_type'].value_counts().reset_index()
        type_dist.columns = ['lesson_type', 'count']
        fig_type = px.pie(type_dist, values='count', names='lesson_type',
                          title='Распределение по типам занятий')
    else:
        fig_type = px.pie(title='Нет данных')

    # График нагрузки преподавателей
    if total_classes > 0:
        teacher_load = filtered_data.groupby('teacher_name')['teacher_load'].sum().reset_index()
        teacher_load = teacher_load.sort_values('teacher_load', ascending=False).head(10)
        fig_teacher = px.bar(teacher_load, x='teacher_name', y='teacher_load',
                             title='Топ-10 преподавателей по нагрузке',
                             labels={'teacher_load': 'Нагрузка (часы)', 'teacher_name': 'Преподаватель'})
    else:
        fig_teacher = px.bar(title='Нет данных')

    return (str(total_classes), str(avg_load), str(total_teachers), str(total_groups),
            fig_institute, fig_date, fig_type, fig_teacher)


# --- КОЛЛБЭК ДЛЯ ОПТИМИЗАЦИИ ---
@app.callback(
    [Output("optimization-results", "children"),
     Output("convergence-graph", "figure"),
     Output("algorithms-comparison", "figure")],
    Input("run-optimization", "n_clicks"),
    [State("opt-algorithm", "value"),
     State("ga-population", "value"),
     State("ga-generations", "value"),
     State("sa-temperature", "value")]
)
def run_optimization(n_clicks, algorithm, population, generations, temperature):
    if n_clicks is None:
        return "Нажмите 'Запустить оптимизацию' для начала", go.Figure(), go.Figure()

    # Настройка параметров алгоритмов
    optimization_engine.ga.population_size = population
    optimization_engine.ga.generations = generations
    optimization_engine.sa.initial_temperature = temperature

    # Запуск оптимизации
    result = optimization_engine.optimize(
        data, teachers, groups, classrooms,
        algorithm=algorithm
    )

    # Результаты
    results_text = [
        html.P(f"✅ Алгоритм: {result['algorithm']}"),
        html.P(f"📊 Fitness: {result['fitness']['fitness']:.4f}"
               if result['fitness'] else "📊 Fitness: не рассчитан"),
        html.P(f"⚠️ Штраф: {result['fitness']['total_penalty']:.2f}"
               if result['fitness'] else ""),
        html.P(f"📈 Жестких нарушений: {result['validation']['hard_constraints']['count']}"
               if result['validation'] else ""),
        html.P(f"📉 Мягких нарушений: {result['validation']['soft_constraints']['count']}"
               if result['validation'] else ""),
    ]

    # График сходимости (для ГА)
    if hasattr(optimization_engine.ga, 'best_fitness_history') and \
            len(optimization_engine.ga.best_fitness_history) > 0:
        generations_list = list(range(len(optimization_engine.ga.best_fitness_history)))
        fig_convergence = go.Figure()
        fig_convergence.add_trace(go.Scatter(
            x=generations_list,
            y=optimization_engine.ga.best_fitness_history,
            mode='lines+markers',
            name='Лучший fitness'
        ))
        fig_convergence.add_trace(go.Scatter(
            x=generations_list,
            y=optimization_engine.ga.avg_fitness_history,
            mode='lines',
            name='Средний fitness'
        ))
        fig_convergence.update_layout(
            title='Сходимость генетического алгоритма',
            xaxis_title='Поколение',
            yaxis_title='Fitness'
        )
    else:
        fig_convergence = go.Figure()
        fig_convergence.update_layout(title='Нет данных о сходимости')

    # Сравнение алгоритмов
    fig_comparison = go.Figure()
    algorithms = ['Генетический', 'Имитация отжига', 'Жадный']
    # Примерные значения для демонстрации
    fitness_values = [0.85, 0.82, 0.75]
    time_values = [45, 30, 5]

    fig_comparison.add_trace(go.Bar(
        name='Fitness',
        x=algorithms,
        y=fitness_values,
        marker_color='#17B897'
    ))
    fig_comparison.add_trace(go.Bar(
        name='Время (сек)',
        x=algorithms,
        y=time_values,
        marker_color='#E12D39',
        yaxis='y2'
    ))

    fig_comparison.update_layout(
        title='Сравнение алгоритмов',
        yaxis=dict(title='Fitness'),
        yaxis2=dict(title='Время (сек)', overlaying='y', side='right')
    )

    return results_text, fig_convergence, fig_comparison


# --- КОЛЛБЭК ДЛЯ РАСПИСАНИЯ ---
@app.callback(
    [Output("schedule-table", "data"),
     Output("schedule-calendar", "figure")],
    Input("apply-schedule-filters", "n_clicks"),
    [State("schedule-group", "value"),
     State("schedule-teacher", "value"),
     State("schedule-week", "value")]
)
def update_schedule(n_clicks, group, teacher, week):
    if n_clicks is None:
        return [], go.Figure()

    filtered = data.copy()

    if group:
        filtered = filtered[filtered['group_name'] == group]
    if teacher:
        filtered = filtered[filtered['teacher_name'] == teacher]

    # Подготовка данных для таблицы
    table_data = filtered.head(20).to_dict('records')

    # Календарь
    if not filtered.empty:
        # Группировка по датам
        daily_counts = filtered.groupby('date').size().reset_index(name='count')
        fig_calendar = px.scatter(daily_counts, x='date', y='count',
                                  size='count', title='Календарь занятий',
                                  labels={'count': 'Количество занятий', 'date': 'Дата'})
    else:
        fig_calendar = px.scatter(title='Нет данных')

    return table_data, fig_calendar


# --- ЗАПУСК ПРИЛОЖЕНИЯ ---
if __name__ == "__main__":
    app.run_server(debug=True, host='127.0.0.1', port=8050)