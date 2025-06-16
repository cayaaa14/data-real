import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout='wide', page_title='Analisis Sosial Media')

@st.cache_data

def load_data():
    url_users = 'https://raw.githubusercontent.com/cayaaa14/data-real/refs/heads/main/user_table.csv'
    url_friends = 'https://raw.githubusercontent.com/cayaaa14/data-real/refs/heads/main/friends_table.csv'
    url_posts = 'https://raw.githubusercontent.com/cayaaa14/data-real/refs/heads/main/posts_table.csv'
    url_reactions = 'https://raw.githubusercontent.com/cayaaa14/data-real/refs/heads/main/reactions_table.csv'

    users = pd.read_csv(url_users)
    friends = pd.read_csv(url_friends)
    posts = pd.read_csv(url_posts)
    reactions = pd.read_csv(url_reactions)

    users['Subscription Date'] = pd.to_datetime(users['Subscription Date'], unit='s')
    posts['Post Date'] = pd.to_datetime(posts['Post Date'], unit='s')
    reactions['Reaction Date'] = pd.to_datetime(reactions['Reaction Date'], unit='s')

    reactions = reactions.dropna(subset=['User'])
    reactions['Reaction Type'] = reactions['Reaction Type'].fillna(reactions['Reaction Type'].mode()[0])
    reactions['Reaction Date'] = reactions['Reaction Date'].fillna(reactions['Reaction Date'].median())

    users = users.drop_duplicates()
    friends = friends.drop_duplicates()
    posts = posts.drop_duplicates()
    reactions = reactions.drop_duplicates()

    users['user_id'] = range(1, len(users) + 1)
    integrated_data = users[['user_id', 'Name', 'Surname', 'Age', 'Subscription Date']].copy()

    all_friends = pd.concat([
        friends[['Friend 1']].rename(columns={'Friend 1': 'user_id'}),
        friends[['Friend 2']].rename(columns={'Friend 2': 'user_id'})
    ])
    friend_stats = all_friends.value_counts('user_id').reset_index()
    friend_stats.columns = ['user_id', 'friend_count']

    posts = posts.rename(columns={'User': 'user_id'})
    posts['post_id'] = range(1, len(posts) + 1)
    post_stats = posts.groupby('user_id')['post_id'].count().reset_index(name='post_count')

    reactions = reactions.rename(columns={'User': 'user_id'})
    reactions['reaction_id'] = range(1, len(reactions) + 1)
    reactions_given = reactions.groupby('user_id')['reaction_id'].count().reset_index(name='reactions_given')

    reactions['post_id'] = reactions['reaction_id'] % len(posts) + 1
    post_reactions = posts.merge(reactions, on='post_id', how='inner')
    reactions_received = post_reactions.groupby('user_id_x')['user_id_y'].count().reset_index()
    reactions_received.columns = ['user_id', 'reactions_received']

    integrated_data = (integrated_data
                       .merge(friend_stats, on='user_id', how='left')
                       .merge(post_stats, on='user_id', how='left')
                       .merge(reactions_given, on='user_id', how='left')
                       .merge(reactions_received, on='user_id', how='left')
                      )

    integrated_data.fillna(0, inplace=True)

    integrated_data['age_group'] = pd.cut(
        integrated_data['Age'], bins=[0, 20, 30, 40, 50, 100],
        labels=['<20', '20-29', '30-39', '40-49', '50+']
    )
    integrated_data['registration_year'] = integrated_data['Subscription Date'].dt.year
    integrated_data['total_activity'] = integrated_data[['friend_count', 'post_count', 'reactions_given']].sum(axis=1)
    integrated_data['engagement_ratio'] = integrated_data['reactions_received'] / (integrated_data['post_count'] + 1)

    return integrated_data, reactions, posts

# Load data
data, reactions, posts = load_data()

st.title("\U0001F4CA Analisis Data Sosial Media")
st.markdown("Visualisasi interaktif untuk **Pertanyaan 1 - 12** dari data sosial media.")

tabs = st.tabs([f"Pertanyaan {i}" for i in range(1, 13)])

with tabs[0]:
    st.subheader("1️⃣ Distribusi Pengguna Berdasarkan Kelompok Usia")
    age_counts = data['age_group'].value_counts().sort_index().reset_index()
    age_counts.columns = ['Kelompok Usia', 'Jumlah Pengguna']
    fig = px.bar(age_counts, x='Kelompok Usia', y='Jumlah Pengguna', color='Kelompok Usia', text='Jumlah Pengguna')
    fig.update_traces(textposition='outside')
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    st.subheader("2️⃣ 10 Pengguna Paling Aktif")
    top_users = data.nlargest(10, 'total_activity')
    fig = px.bar(top_users, y='Name', x='total_activity', orientation='h',
                 labels={'total_activity': 'Total Aktivitas', 'Name': 'Nama'},
                 color='total_activity', color_continuous_scale='Teal')
    fig.update_layout(yaxis=dict(autorange='reversed'))
    st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    st.subheader("3️⃣ Jenis Reaksi Paling Populer")
    reaction_counts = reactions['Reaction Type'].value_counts().reset_index()
    reaction_counts.columns = ['Jenis Reaksi', 'Jumlah']
    fig = px.pie(reaction_counts, names='Jenis Reaksi', values='Jumlah', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

with tabs[3]:
    st.subheader("4️⃣ Proporsi Pengguna Berdasarkan Level Aktivitas")
    def categorize(row):
        if row['total_activity'] == 0:
            return 'Tidak Aktif'
        elif row['total_activity'] <= 5:
            return 'Rendah'
        elif row['total_activity'] <= 15:
            return 'Sedang'
        elif row['total_activity'] <= 30:
            return 'Tinggi'
        else:
            return 'Sangat Aktif'

    data['activity_level'] = data.apply(categorize, axis=1)
    level_counts = data['activity_level'].value_counts().reset_index()
    level_counts.columns = ['Level Aktivitas', 'Jumlah']
    fig = px.pie(level_counts, names='Level Aktivitas', values='Jumlah', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

with tabs[4]:
    st.subheader("5️⃣ Distribusi Usia Pengguna")
    fig = px.histogram(data, x='Age', nbins=20, marginal='box', color_discrete_sequence=['#4ECDC4'])
    st.plotly_chart(fig, use_container_width=True)

with tabs[5]:
    st.subheader("6️⃣ Distribusi Engagement Ratio")
    posting_users = data[data['post_count'] > 0]
    fig = px.histogram(posting_users, x='engagement_ratio', nbins=30, color_discrete_sequence=['#FFEAA7'])
    st.plotly_chart(fig, use_container_width=True)

with tabs[6]:
    st.subheader("7️⃣ Jumlah Postingan per Jenis Post")
    post_type = posts['Post Type'].value_counts().reset_index()
    post_type.columns = ['Jenis Post', 'Jumlah']
    fig = px.bar(post_type, x='Jenis Post', y='Jumlah', color='Jumlah', color_continuous_scale='Blues')
    st.plotly_chart(fig, use_container_width=True)

with tabs[7]:
    st.subheader("8️⃣ Pola Aktivitas per Kelompok Usia")
    stats = data.groupby('age_group')[['friend_count', 'post_count', 'reactions_given', 'reactions_received']].mean().reset_index()
    fig = px.line(stats, x='age_group', y=['friend_count', 'post_count', 'reactions_given', 'reactions_received'],
                  labels={'value': 'Rata-rata', 'age_group': 'Kelompok Usia'},
                  markers=True)
    st.plotly_chart(fig, use_container_width=True)

with tabs[8]:
    st.subheader("9️⃣ Hubungan Jumlah Teman vs Jumlah Postingan")
    fig = px.scatter(data, x='friend_count', y='post_count', color='Age', size='total_activity',
                     labels={'friend_count': 'Jumlah Teman', 'post_count': 'Jumlah Postingan'})
    st.plotly_chart(fig, use_container_width=True)

with tabs[9]:
    st.subheader("🔟 Usia vs Total Aktivitas")
    fig = px.scatter(data, x='Age', y='total_activity', color='friend_count', size='post_count',
                     labels={'Age': 'Usia', 'total_activity': 'Total Aktivitas'})
    st.plotly_chart(fig, use_container_width=True)

with tabs[10]:
    st.subheader("1️⃣1️⃣ Korelasi Antar Variabel Aktivitas")
    corr = data[['Age', 'friend_count', 'post_count', 'reactions_given', 'reactions_received']].corr()
    fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu', aspect="auto")
    st.plotly_chart(fig, use_container_width=True)

with tabs[11]:
    st.subheader("1️⃣2️⃣ Aktivitas Berdasarkan Usia & Tahun Registrasi")
    heatmap_data = data.groupby(['age_group', 'registration_year'])['total_activity'].mean().reset_index()
    fig = px.density_heatmap(heatmap_data, x='registration_year', y='age_group', z='total_activity',
                             color_continuous_scale='YlOrRd', nbinsx=len(data['registration_year'].unique()))
    st.plotly_chart(fig, use_container_width=True)
