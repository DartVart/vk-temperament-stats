import streamlit as st
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import pymongo
from datetime import datetime, date, timezone, timedelta
import time

TRANSLATIONS = {
    'sanguine': 'Сангвиники',
    'phlegmatic': 'Флегматики',
    'melancholic': 'Меланхолики',
    'choleric': 'Холерики',
}

if 'db' not in st.session_state:
    mongo_url = st.secrets["mongo_url"]
    db_name = st.secrets["db_name"]
    client = pymongo.MongoClient(mongo_url)
    db = client[db_name]
    st.session_state['db'] = db

st.header("Темперамент аудитории")

if 'time' not in st.session_state:
    threshold_time = st.time_input("Время отчета", value=None)
else:
    threshold_time = st.session_state['time']

if threshold_time is not None:
    current_date = date.today()
    threshold_datetime = datetime(
        current_date.year, current_date.month, current_date.day,
        threshold_time.hour + int(st.secrets["timezone_delta"]), threshold_time.minute, 0, 0
    )
    unix_timestamp_threshold = time.mktime(threshold_datetime.timetuple()) * 1000

    recent_predictions_events = st.session_state['db']["events"].find(
        {
            'timestamp': {'$gt': unix_timestamp_threshold},
            'name': 'user_clicked_check_me_button'
        },
        {'user_id': 1}
    )
    recent_ids = list(set(pred['user_id'] for pred in recent_predictions_events))
    recent_predictions = list(st.session_state['db']["predictions"].find({'prediction_user_id': {'$in': recent_ids}}))

    count = st_autorefresh(interval=2000, limit=10000, key="temperament")

    results = {}
    for recent_prediction in recent_predictions:
        if ((recent_prediction['prediction_user_id'] in results and
                recent_prediction['predicted_at'] > results[recent_prediction['prediction_user_id']]['predicted_at']) or
                (recent_prediction['prediction_user_id'] not in results)):
            results[recent_prediction['prediction_user_id']] = {
                'predicted_at': recent_prediction['predicted_at'],
                'result': recent_prediction['temperament']
            }

    temperaments = {
        'sanguine': 0,
        'phlegmatic': 0,
        'melancholic': 0,
        'choleric': 0,
    }

    for res in results.values():
        temperaments[res['result']] += 1

    fig = go.Figure([go.Bar(
        x=list(TRANSLATIONS[k] for k in temperaments.keys()),
        y=list(temperaments.values()),
        marker=dict(color='#21BA72'),
    )])
    st.plotly_chart(fig)
