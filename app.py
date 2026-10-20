from datetime import datetime
import os
import pandas as pd
import plotly.express as px
import streamlit as st

# ==========================================
# 定数・設定
# ==========================================
CSV_FILE = "movies.csv"

CATEGORY_LIST = ["映画", "ドラマ", "アニメ", "その他"]
GENRE_LIST = [
    "サスペンス・ミステリー",
    "SF",
    "アクション",
    "コメディ",
    "ドラマ",
    "恋愛",
    "ホラー",
    "ファンタジー",
    "ドキュメンタリー",
    "アニメ",
    "その他",
]
REGION_LIST = ["日本", "海外", "韓国", "中国", "台湾", "その他"]


# ==========================================
# データ入出力関数
# ==========================================
def load_data():
  """CSVファイルからデータを読み込み、不足している列を補正する"""
  expected_columns = [
      "タイトル",
      "種別",
      "ジャンル",
      "国・地域",
      "視聴日",
      "評価",
      "感想",
  ]

  if not os.path.exists(CSV_FILE):
    return pd.DataFrame(columns=expected_columns)

  df = pd.read_csv(CSV_FILE, encoding="utf-8")

  # 旧カラム名の互換性対応
  if "地域" in df.columns and "国・地域" not in df.columns:
    df = df.rename(columns={"地域": "国・地域"})

  # 欠損列の初期化
  for col in expected_columns:
    if col not in df.columns:
      if col in ["ジャンル", "国・地域"]:
        df[col] = "その他"
      elif col == "種別":
        df[col] = "映画"
      else:
        df[col] = ""

  return df


def save_data(df):
  """データフレームをCSVファイルに保存する"""
  df.to_csv(CSV_FILE, index=False, encoding="utf-8")


# ==========================================
# UIパーツ用関数（再利用・整理）
# ==========================================
def render_summary_metrics(df):
  """画面上部のサマリー指標（総視聴数、今月の数、平均評価）を表示する"""
  if df.empty:
    return

  current_year_month = datetime.now().strftime("%Y-%m")
  df_calc = df.copy()
  df_calc["年月"] = (
      pd.to_datetime(df_calc["視聴日"], errors="coerce")
      .dt.strftime("%Y-%m")
  )

  # 今月の視聴データ
  df_this_month = df_calc[df_calc["年月"] == current_year_month]
  this_month_count = len(df_this_month)

  target_categories = ["映画", "ドラマ", "アニメ"]

  # 今月の種別内訳
  this_month_breakdown = " / ".join([
      f"{cat}:{len(df_this_month[df_this_month['種別'] == cat])}"
      for cat in target_categories
  ])

  # 総視聴数の種別内訳
  total_count = len(df)
  total_breakdown = " / ".join(
      [f"{cat}:{len(df[df['種別'] == cat])}" for cat in target_categories]
  )

  # 平均評価
  avg_rating = round(df["評価"].astype(float).mean(), 1) if not df.empty else 0

  # メトリック表示（3カラム）
  col1, col2, col3 = st.columns(3)
  with col1:
    st.metric(
        label="総視聴作品数",
        value=f"{total_count}",
        delta=total_breakdown if total_count > 0 else "",
    )
  with col2:
    st.metric(
        label="今月の作品数",
        value=f"{this_month_count}",
        delta=this_month_breakdown if this_month_count > 0 else "",
    )
  with col3:
    st.metric(label="平均評価", value=f"⭐ {avg_rating} / 5")


def filter_and_sort_data(df):
  """検索フィルターと並び替え条件を適用してデータフレームを返す"""
  filtered_df = df.copy()

  with st.expander("🔍 検索・並び替えフィルターを開く", expanded=False):
    if st.button("🔄 検索条件をリセット"):
      for key in [
          "search_keyword",
          "filter_type",
          "filter_genre",
          "filter_region",
          "only_favorite",
          "sort_order",
      ]:
        if key in st.session_state:
          del st.session_state[key]
      st.rerun()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
      keyword = st.text_input("キーワード検索", "", key="search_keyword")
    with col2:
      f_type = st.selectbox(
          "種別で絞り込み", ["すべて"] + CATEGORY_LIST, key="filter_type"
      )
    with col3:
      f_genre = st.selectbox(
          "ジャンルで絞り込み", ["すべて"] + GENRE_LIST, key="filter_genre"
      )
    with col4:
      f_region = st.selectbox(
          "国・地域で絞り込み", ["すべて"] + REGION_LIST, key="filter_region"
      )

    only_fav = st.checkbox(
        "お気に入り (星5) のみを表示する", key="only_favorite"
    )
    sort_by = st.selectbox(
        "並び替え",
        [
            "視聴日（新しい順）",
            "視聴日（古い順）",
            "評価が高い順",
            "評価が低い順",
        ],
        key="sort_order",
    )

  # フィルタリング処理
  if keyword:
    filtered_df = filtered_df[
        filtered_df["タイトル"].str.contains(keyword, case=False, na=False)
        | filtered_df["感想"].str.contains(keyword, case=False, na=False)
    ]
  if f_type != "すべて":
    filtered_df = filtered_df[filtered_df["種別"] == f_type]
  if f_genre != "すべて":
    filtered_df = filtered_df[filtered_df["ジャンル"] == f_genre]
  if f_region != "すべて":
    filtered_df = filtered_df[filtered_df["国・地域"] == f_region]
  if only_fav:
    filtered_df = filtered_df[filtered_df["評価"] == 5]

  # ソート処理
  if sort_by == "視聴日（新しい順）":
    filtered_df = filtered_df.sort_values(by="視聴日", ascending=False)
  elif sort_by == "視聴日（古い順）":
    filtered_df = filtered_df.sort_values(by="視聴日", ascending=True)
  elif sort_by == "評価が高い順":
    filtered_df = filtered_df.sort_values(by="評価", ascending=False)
  elif sort_by == "評価が低い順":
    filtered_df = filtered_df.sort_values(by="評価", ascending=True)

  return filtered_df


def build_ai_prompt(
    df, selected_titles, selected_services, mood_input
):
  """AIおすすめ用のプロンプト文字列を組み立てて生成する"""
  all_watched_titles = df["タイトル"].dropna().unique().tolist()
  watched_titles_text = (
      ", ".join(all_watched_titles)
      if all_watched_titles
      else "視聴済みデータなし"
  )

  services_text = (
      ", ".join(selected_services)
      if selected_services
      else "特に指定なし（どのサービスでも可）"
  )
  selected_history_text = (
      ", ".join(selected_titles) if selected_titles else "特になし"
  )
  mood_text = mood_input if mood_input.strip() else "特になし（おまかせ）"

  prompt = f"""あなたは優秀で映画・ドラマに精通したプロのソムリエです。
以下の「ユーザーの好みの参考作品（タイトル）」と「現在の気分・要望」、「利用中の動画配信サービス」をふまえて、ユーザーが気に入りそうな次の新しい作品を3つ提案してください。

【出力時の必須条件】
1. 各作品について、以下の内容を必ず含めてください：
   - 作品タイトル
   - 簡単なあらすじ（ネタバレなし）
   - この作品を選んだ理由（ユーザーの好みの傾向からどこに刺さりそうか）
2. 指定された動画配信サービスで視聴できる作品を中心に選んでください。

【制約事項：重要】
- 以下の【視聴済み作品リスト】に含まれる作品は、すでに視聴済みのため絶対に提案しないでください。必ずこれら以外の作品を提案してください。

【視聴済み作品リスト（除外対象：全{len(all_watched_titles)}件）】
{watched_titles_text}

【利用中の動画配信サービス】
{services_text}

【ユーザーの好みの参考作品（お気に入り・選択作品）】
{selected_history_text}

【現在のユーザーの気分・要望】
{mood_text}
"""
  return prompt


# ==========================================
# メインアプリケーションの実行
# ==========================================
st.title("映画・ドラマ視聴ログ")

# データのロード
df = load_data()

# セッションステート初期化
if "form_success_message" not in st.session_state:
  st.session_state.form_success_message = ""
if "form_error_message" not in st.session_state:
  st.session_state.form_error_message = ""

# 上部サマリーの表示
render_summary_metrics(df)

# タブの作成
tab1, tab2, tab3 = st.tabs([
    "📂 記録データ",
    "📊 分析レポート",
    "🧙‍♂️ AIおすすめレコメンド",
])

# ------------------------------------------
# タブ1: 記録データ一覧 ＆ 管理
# ------------------------------------------
with tab1:
  st.subheader("記録データ一覧 ＆ 管理")

  # 新しい作品を記録するフォーム
  with st.expander("✏️ 新しい作品を記録する", expanded=False):
    if st.session_state.form_success_message:
      st.success(st.session_state.form_success_message)
      st.session_state.form_success_message = ""
    if st.session_state.form_error_message:
      st.error(st.session_state.form_error_message)
      st.session_state.form_error_message = ""

    with st.form("movie_form_clean", clear_on_submit=True):
      title = st.text_input("タイトル")

      col_f1, col_f2 = st.columns(2)
      with col_f1:
        category = st.selectbox("種別", CATEGORY_LIST)
        region = st.selectbox("国・地域", REGION_LIST)
      with col_f2:
        genre = st.selectbox("ジャンル", GENRE_LIST)
        watched_date = st.date_input("視聴日")

      rating = st.slider("評価 (星5段階)", 1, 5, 3)
      comment = st.text_area("感想・メモ")

      submitted = st.form_submit_button("登録する")

      if submitted:
        if title:
          is_already_watched = title in df["タイトル"].values

          new_data = pd.DataFrame({
              "タイトル": [title],
              "種別": [category],
              "ジャンル": [genre],
              "国・地域": [region],
              "視聴日": [str(watched_date)],
              "評価": [rating],
              "感想": [comment],
          })
          df = pd.concat([df, new_data], ignore_index=True)
          save_data(df)

          if is_already_watched:
            st.session_state.form_success_message = (
                f"「{title}」を登録しました！（※同名の作品がすでに登録されています）"
            )
          else:
            st.session_state.form_success_message = (
                f"「{title}」を登録しました！"
            )
          st.session_state.form_error_message = ""
          st.rerun()
        else:
          st.error("タイトルを入力してください。")

  if df.empty:
    st.info("まだ記録がありません。上のフォームから作品を追加してみましょう！")
  else:
    # 検索・並び替えを適用したデータフレームを取得
    filtered_df = filter_and_sort_data(df)

    display_columns = [
        "タイトル",
        "種別",
        "ジャンル",
        "国・地域",
        "視聴日",
        "評価",
        "感想",
    ]
    st.dataframe(
        filtered_df[display_columns], use_container_width=True, hide_index=True
    )

    # データの編集・削除管理セクション
    with st.expander("🛠️ データの編集・削除を行う"):
      edit_tab, delete_tab = st.tabs(
          ["📝 データを編集する", "🗑️ データを削除する"]
      )

      df_with_index = df.copy()
      df_with_index["一意キー"] = (
          df_with_index["タイトル"]
          + " (視聴日: "
          + df_with_index["視聴日"].astype(str)
          + ")"
      )
      item_options = ["選択してください"] + list(df_with_index["一意キー"])

      with edit_tab:
        edit_target_key = st.selectbox(
            "編集する作品を選択", item_options, key="edit_select"
        )
        if edit_target_key != "選択してください":
          target_row_idx = df_with_index[
              df_with_index["一意キー"] == edit_target_key
          ].index[0]
          target_row = df.loc[target_row_idx]

          with st.form("edit_form"):
            st.write(
                f"「{target_row['タイトル']}」({target_row['視聴日']})"
                " の情報を変更します"
            )
            new_title = st.text_input("タイトル", value=target_row["タイトル"])

            cat_index = (
                CATEGORY_LIST.index(target_row["種別"])
                if target_row["種別"] in CATEGORY_LIST
                else 0
            )
            new_cat = st.selectbox("種別", CATEGORY_LIST, index=cat_index)

            genre_index = (
                GENRE_LIST.index(target_row["ジャンル"])
                if target_row["ジャンル"] in GENRE_LIST
                else 0
            )
            new_genre = st.selectbox("ジャンル", GENRE_LIST, index=genre_index)

            region_val = (
                target_row["国・地域"]
                if "国・地域" in target_row and pd.notnull(target_row["国・地域"])
                else "その他"
            )
            region_index = (
                REGION_LIST.index(region_val) if region_val in REGION_LIST else 0
            )
            new_region = st.selectbox(
                "国・地域", REGION_LIST, index=region_index
            )

            try:
              default_date = pd.to_datetime(target_row["視聴日"]).date()
            except:
              default_date = pd.Timestamp.today().date()
            new_date = st.date_input("視聴日", value=default_date)

            new_rating = st.slider(
                "評価 (星5段階)",
                1,
                5,
                int(target_row["評価"]) if pd.notnull(target_row["評価"]) else 3,
            )
            new_comment = st.text_area(
                "感想・メモ",
                value=str(target_row["感想"])
                if pd.notnull(target_row["感想"])
                else "",
            )

            if st.form_submit_button("変更を保存する"):
              df.loc[target_row_idx, "タイトル"] = new_title
              df.loc[target_row_idx, "種別"] = new_cat
              df.loc[target_row_idx, "ジャンル"] = new_genre
              df.loc[target_row_idx, "国・地域"] = new_region
              df.loc[target_row_idx, "視聴日"] = str(new_date)
              df.loc[target_row_idx, "評価"] = new_rating
              df.loc[target_row_idx, "感想"] = new_comment

              save_data(df)
              if "edit_select" in st.session_state:
                del st.session_state["edit_select"]
              st.success(f"「{new_title}」の情報を更新しました！")
              st.rerun()

      with delete_tab:
        delete_target_key = st.selectbox(
            "削除する作品を選択", item_options, key="delete_select"
        )
        if delete_target_key != "選択してください":
          target_row_idx = df_with_index[
              df_with_index["一意キー"] == delete_target_key
          ].index[0]
          target_row = df.loc[target_row_idx]

          if st.button("この作品を削除する", type="primary"):
            df = df.drop(target_row_idx).reset_index(drop=True)
            save_data(df)
            st.success(
                f"「{target_row['タイトル']}」({target_row['視聴日']})"
                " を削除しました！"
            )
            st.rerun()

    # CSVダウンロード ＆ 全データリセットセクション
    st.markdown("<br>", unsafe_allow_html=True)
    if "show_download_confirm" not in st.session_state:
      st.session_state.show_download_confirm = False

    if not st.session_state.show_download_confirm:
      if st.button("📥 視聴記録をCSVとしてダウンロード"):
        st.session_state.show_download_confirm = True
        st.rerun()
    else:
      st.info("CSVファイルをダウンロードしますか？")
      col_dl1, col_dl2 = st.columns(2)
      with col_dl1:
        st.download_button(
            label="はい、ダウンロード",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="my_movie_records.csv",
            mime="text/csv",
        )
      with col_dl2:
        if st.button("キャンセル", key="cancel_dl"):
          st.session_state.show_download_confirm = False
          st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if "reset_step" not in st.session_state:
      st.session_state.reset_step = 0

    if st.session_state.reset_step == 0:
      if st.button("❌ 全データをリセット（初期化）"):
        st.session_state.reset_step = 1
        st.rerun()
    elif st.session_state.reset_step == 1:
      st.warning("⚠️ 本当にすべてのデータをリセットしますか？")
      col_rs1, col_rs2 = st.columns(2)
      with col_rs1:
        if st.button("はい、リセットする"):
          st.session_state.reset_step = 2
          st.rerun()
      with col_rs2:
        if st.button("キャンセル", key="cancel_rs_1"):
          st.session_state.reset_step = 0
          st.rerun()
    elif st.session_state.reset_step == 2:
      st.error(
          "🚨【最終確認】この操作を行うと、これまでの記録データがすべて完全に消去され、元に戻せません。本当に実行しますか？"
      )
      col_rs3, col_rs4 = st.columns(2)
      with col_rs3:
        if st.button("はい、本当にすべてのデータを削除する", type="primary"):
          if os.path.exists(CSV_FILE):
            os.remove(CSV_FILE)
          st.session_state.reset_step = 0
          st.success("全データをリセットしました。")
          st.rerun()
      with col_rs4:
        if st.button("キャンセル", key="cancel_rs_2"):
          st.session_state.reset_step = 0
          st.rerun()

# ------------------------------------------
# タブ2: 視聴データの分析レポート
# ------------------------------------------
with tab2:
  st.subheader("視聴データの分析レポート")
  if df.empty:
    st.info("データがありません。作品を記録するとグラフが表示されます。")
  else:
    col1, col2 = st.columns(2)

    with col1:
      st.markdown("##### 💿 項目別の割合")
      chart_target = st.radio(
          "表示項目",
          ["ジャンル別", "国・地域別", "評価別"],
          horizontal=True,
          key="pie_target",
      )

      if chart_target == "ジャンル別":
        counts = df["ジャンル"].value_counts().reset_index()
        counts.columns = ["項目", "count"]
      elif chart_target == "国・地域別":
        counts = df["国・地域"].value_counts().reset_index()
        counts.columns = ["項目", "count"]
      else:
        counts = df["評価"].astype(str).value_counts().reset_index()
        counts.columns = ["項目", "count"]
        counts["項目"] = counts["項目"] + "評価"

      fig_pie = px.pie(counts, names="項目", values="count", hole=0.4)
      st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
      st.markdown("##### 📈 視聴数の推移")
      if "視聴日" in df.columns:
        df_temp = df.copy()
        df_temp["dt"] = pd.to_datetime(df_temp["視聴日"], errors="coerce")

        time_unit = st.radio(
            "表示単位", ["月別", "年別"], horizontal=True, key="time_unit_radio"
        )
        if time_unit == "月別":
          df_temp["年"] = df_temp["dt"].dt.year.astype(str)
          available_years = sorted(df_temp["年"].unique())
          selected_year = st.selectbox(
              "表示する年を選択", ["全期間"] + available_years, key="selected_year_sb"
          )

          if selected_year == "全期間":
            df_temp["年月"] = df_temp["dt"].dt.strftime("%Y%m")
            min_date, max_date = df_temp["dt"].min(), df_temp["dt"].max()

            if pd.notnull(min_date) and pd.notnull(max_date):
              all_months = pd.date_range(
                  start=min_date,
                  end=max_date,
                  freq="MS",
              ).strftime("%Y%m").tolist()
              
              counts = (
                  df_temp["年月"]
                  .value_counts()
                  .reindex(all_months, fill_value=0)
                  .reset_index()
              )
              counts.columns = ["期間", "視聴数"]
              
              # 軸用の表示ラベル（1月だけ年号、ほかは空欄）
              counts["表示ラベル"] = counts["期間"].apply(
                  lambda x: x[:4] if x.endswith("01") else ""
              )
              
              fig = px.bar(
                  counts,
                  x="期間",
                  y="視聴数",
                  range_y=[0, 30],
                  category_orders={"期間": all_months}
              )
              
              # ★ここでホバーの設定と軸の設定をまとめて適用する
              fig.update_traces(hovertemplate="期間: %{x}<br>視聴数: %{y}<extra></extra>")
              fig.update_layout(
                  xaxis=dict(
                      type="category",
                      tickmode="array",
                      tickvals=counts["期間"],
                      ticktext=counts["表示ラベル"],
                      tickangle=0,
                  )
              )
              
              st.plotly_chart(fig, use_container_width=True)
            else:
              st.info("データがありません")
          else:
            df_filtered_year = df_temp[df_temp["年"] == selected_year]
            all_months = [f"{selected_year}{m:02d}" for m in range(1, 13)]
            
            df_filtered_year["年月"] = (
                df_filtered_year["dt"].dt.strftime("%Y%m")
            )
            counts = (
                df_filtered_year["年月"]
                .value_counts()
                .reindex(all_months, fill_value=0)
                .reset_index()
            )
            counts.columns = ["期間", "視聴数"]
            
            # 軸用の表示ラベル（月だけ表示）
            counts["表示ラベル"] = counts["期間"].apply(lambda x: x[4:] + "月")
            
            fig = px.bar(
                counts,
                x="期間",
                y="視聴数",
                range_y=[0, 30],
                category_orders={"期間": all_months}
            )
            
            # ★こちらも同様に update_traces でホバーを設定
            fig.update_traces(hovertemplate="期間: %{x}<br>視聴数: %{y}<extra></extra>")
            fig.update_layout(
                xaxis=dict(
                    type="category",
                    tickmode="array",
                    tickvals=counts["期間"],
                    ticktext=counts["表示ラベル"],
                    tickangle=0,
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
          df_temp["期間"] = df_temp["dt"].dt.year.astype(str)
          counts = df_temp["期間"].value_counts().sort_index().reset_index()
          counts.columns = ["期間", "視聴数"]
          st.bar_chart(counts.set_index("期間"))

# ------------------------------------------
# タブ3: AIおすすめレコメンド
# ------------------------------------------
with tab3:
  st.subheader("プロンプトコピー型 AIおすすめレコメンド")
  st.write(
      "視聴履歴や今の気分、お使いの動画配信サービスに合わせて、AIにそのまま貼り付けて使えるプロンプトを自動生成します！"
  )

  if df.empty:
    st.warning("まずは作品を登録してください！")
  else:
    if "recommend_reset_count" not in st.session_state:
      st.session_state.recommend_reset_count = 0

    if st.button("🔄 入力条件をリセットする"):
      st.session_state.recommend_reset_count += 1
      if "random_sampled" in st.session_state:
        del st.session_state["random_sampled"]
      st.rerun()

    rc = st.session_state.recommend_reset_count
    mode_key, editor_key, mood_key = (
        f"rec_mode_{rc}",
        f"recommend_editor_{rc}",
        f"rec_mood_{rc}",
    )

    selection_mode = st.radio(
        "参考にする作品の選び方を選んでください",
        [
            "① テーブルから自分でチェックボックスで選択",
            "② 評価5〜4の作品からランダムで3作品を自動選択",
        ],
        key=mode_key,
    )

    selected_titles_for_prompt = []

    if selection_mode == "① テーブルから自分でチェックボックスで選択":
      st.write(
          "下のテーブルの「選択」列にチェックを入れてください。"
      )

      display_df = df.copy()
      display_df["視聴日_dt"] = pd.to_datetime(
          display_df["視聴日"], errors="coerce"
      )
      display_df = display_df.sort_values(
          by="視聴日_dt", ascending=False
      ).drop(columns=["視聴日_dt"])

      if "選択" not in display_df.columns:
        display_df.insert(0, "選択", False)

      edited_df = st.data_editor(
          display_df,
          hide_index=True,
          key=editor_key,
          column_config={"選択": st.column_config.CheckboxColumn(required=True)},
      )

      selected_rows = edited_df[edited_df["選択"] == True]
      selected_titles_for_prompt = selected_rows["タイトル"].tolist()
      st.info(f"現在 **{len(selected_titles_for_prompt)}作品** が選択されています。")

    else:
      st.write(
          "「評価5または4」の作品プールから、ランダムで3作品を自動ピックアップします。"
      )
      target_pool = df[df["評価"].isin([4, 5])] if "評価" in df.columns else df

      if st.button("🎲 3作品をランダム選出する", key=f"random_btn_{rc}"):
        sampled = (
            target_pool.sample(n=3)
            if len(target_pool) >= 3
            else target_pool
        )
        st.session_state["random_sampled"] = sampled["タイトル"].tolist()

      if "random_sampled" in st.session_state:
        selected_titles_for_prompt = st.session_state["random_sampled"]
        st.success(f"選出された作品: {', '.join(selected_titles_for_prompt)}")
      else:
        st.info(
            "上のボタンを押すと、評価5〜4の作品からランダムに3作品が選ばれます。"
        )

    st.markdown("##### 📺 利用中の動画配信サービス")
    selected_services = st.multiselect(
        "現在利用しているサービスを選択してください",
        ["Netflix", "Amazon Prime Video", "Disney+", "U-NEXT"],
        default=["Netflix", "Amazon Prime Video"],
        key="rec_services",
    )

    st.markdown("##### 🍃 いまの気分や要望（自由入力）")
    mood_input = st.text_area(
        "例：「ハッピーエンドで爽快感のある作品がいい」「頭を使わないコメディ」「どんでん返しがすごいミステリー」など",
        placeholder="ここに今の気分を入力してください（未入力でもOK）...",
        key=mood_key,
    )

    # プロンプト生成関数を呼び出し
    generated_prompt = build_ai_prompt(
        df, selected_titles_for_prompt, selected_services, mood_input
    )

    st.markdown("---")
    st.subheader("生成されたプロンプト")
    st.write(
        "右上の **コピーボタン（📋アイコン）** をクリックすると、プロンプトをワンクリックでコピーできます！そのままお好みのAIに貼り付けてください。"
    )
    st.code(generated_prompt, language="markdown")
