from database import session, Author, Genre, Book, AudioFile

def add_game_of_thrones():
    """Скрипт для добавления 'Игры Престолов' и всех ее глав в БД."""
    
    # --- Данные о книге ---
    book_title = "Игра Престолов"
    author_name = "Джордж Р. Р. Мартин"
    genre_name = "Фэнтези"
    
    # --- Список глав, сформированный из вашего файла ---
    chapters = [
        {"title": "01 Пролог", "file_id": "CQACAgIAAxkBAAMUaFFzk3cjjJDivmDwkilFKLji-8IAArNwAAJwGpBK4dSg0wTpk3k2BA"},
        {"title": "02 Бран I", "file_id": "CQACAgIAAxkBAAMWaFFz8XWYhy5ciRrJTwSX1WUMFCAAAi51AALoO5BK2cb9YCqbJBk2BA"},
        {"title": "03 Кейтилин I", "file_id": "CQACAgIAAxkBAAMYaFF0JtMl1ddoekAG3BGK0Ij6ydAAAjF1AALoO5BKt5Hb9C2Yv4s2BA"},
        {"title": "04 Дейенерис I", "file_id": "CQACAgIAAxkBAAMaaFF0PhaQl5-nYWDsjvUOwORyIH0AAjR1AALoO5BK6FWwYj18ASM2BA"},
        {"title": "05 Эддард I", "file_id": "CQACAgIAAxkBAAMcaFF0ceoeIhmFrcp2N1xCwSJmu04AAjd1AALoO5BKcBGV59QDZ202BA"},
        {"title": "06 Джон I", "file_id": "CQACAgIAAxkBAAMeaFF0kc3yn4cKO-rxtbT5rCknR6MAAjp1AALoO5BKCnJH3DpcmYI2BA"},
        {"title": "07 Кейтилин II", "file_id": "CQACAgIAAxkBAAMgaFF0udLbqoBOs1gY2jTfllgIF9IAAkJ1AALoO5BKo6v6W7Y8yGE2BA"},
        {"title": "08 Арья I", "file_id": "CQACAgIAAxkBAAMiaFF00s28o2QS1XJvTLj9jTG0JTMAAkd1AALoO5BKhMnWr3KSocU2BA"},
        {"title": "09 Бран II", "file_id": "CQACAgIAAxkBAAMkaFF09ZIU-UivNye5Og6LCC_YQc8AAkl1AALoO5BKUOd9b9HEE-A2BA"},
        {"title": "10 Тирион I", "file_id": "CQACAgIAAxkBAAMmaFF1EuK9gBXqAAFDwDJ0qDy3nDA_AAJMdQAC6DuQSvoGoCYKo5JyNgQ"},
        {"title": "11 Джон II", "file_id": "CQACAgIAAxkBAAMoaFF1KdQOLpucPs_X6uWaHBIWnNIAAlB1AALoO5BKLDIw8AABcHa5NgQ"},
        {"title": "12 Дейенерис II", "file_id": "CQACAgIAAxkBAAMqaFF1QEj9Emz5r2W4zL9vco5r7aQAAlN1AALoO5BKZQqjyxvTtuo2BA"},
        {"title": "13 Эддард II", "file_id": "CQACAgIAAxkBAAMsaFF1XokzQGmL5D0En8ZrhNDjE8QAAlZ1AALoO5BKUselJNVF5fU2BA"},
        {"title": "14 Тирион II", "file_id": "CQACAgIAAxkBAAMuaFF1eb6F4jyasr9mfceNREZhdzIAAlp1AALoO5BKIyS6UVuRY5Q2BA"},
        {"title": "15 Кейтилин III", "file_id": "CQACAgIAAxkBAAMwaFF1j9NPRc4VqwoHFlFV3EtE-2cAAl51AALoO5BKySc_KJX8zhU2BA"},
        {"title": "16 Санса I", "file_id": "CQACAgIAAxkBAAMyaFF1qnaIlRwTNuzPFoaaMfHXnBMAAmF1AALoO5BKusLR4alk-Jw2BA"},
        {"title": "17 Эддард III", "file_id": "CQACAgIAAxkBAAM0aFF1vhX64gQ34mCwmDJHiU4sI1gAAmJ1AALoO5BK02hs4PZEz0k2BA"},
        {"title": "18 Бран III", "file_id": "CQACAgIAAxkBAAM2aFF11bezqkL7bFdqyrV0nZAxWfoAAmN1AALoO5BK5UZeElZLOGo2BA"},
        {"title": "19 Кейтилин IV", "file_id": "CQACAgIAAxkBAAM4aFF17ddvxXAzUKNaqdcdyEZFxhIAAmZ1AALoO5BKePAX1Qt9lLs2BA"},
        {"title": "20 Джон III", "file_id": "CQACAgIAAxkBAAM6aFF2CUZDnnnOsViy3_1mUbfjlRcAAmd1AALoO5BKVg2nC-hwdfs2BA"},
        {"title": "21 Эддард IV", "file_id": "CQACAgIAAxkBAAM8aFF2ModVrFzTfuSqy1xIhVEG3u8AAmx1AALoO5BKYzh6IqQcqAABNgQ"},
        {"title": "22 Тирион III", "file_id": "CQACAgIAAxkBAAM-aFF2v712c8B_yFYBu-bZ5qBkzJIAAnd1AALoO5BKEz24A99CF7g2BA"},
        {"title": "23 Арья II", "file_id": "CQACAgIAAxkBAANAaFF24vGsdjLn0B9wbk81XIVGv0sAAn11AALoO5BKIrPJLaoNI3A2BA"},
        {"title": "24 Дейенерис III", "file_id": "CQACAgIAAxkBAANCaFF2-EQw1lQQ2_3epRnh_w0g51cAAoB1AALoO5BKPNtl0hrZd-w2BA"},
        {"title": "25 Бран IV", "file_id": "CQACAgIAAxkBAANEaFF3HN_xIyjOPd-SUH_2G9JNWiAAAoR1AALoO5BKjvBU_YQ9_ps2BA"},
        {"title": "26 Эддард V", "file_id": "CQACAgIAAxkBAANGaFF3NrbXGTZaUW88_3RJptXTvqgAAod1AALoO5BKJCk-A0VjNAo2BA"},
        {"title": "27 Джон IV", "file_id": "CQACAgIAAxkBAANIaFF3TNlXwMnJGKqFW9nmj6tK22sAAoh1AALoO5BKkjHtlhsF6aQ2BA"},
        {"title": "28 Эддард VI", "file_id": "CQACAgIAAxkBAANKaFF3aOjBn2pQf6WhG9K8oCo5YVMAAop1AALoO5BKf5W_0y_G2io2BA"},
        {"title": "29 Кейтилин V", "file_id": "CQACAgIAAxkBAANMaFF3kS6JGrg6dH7zmCXYCVsqi3oAAo11AALoO5BKngIMWTzfbEk2BA"},
        {"title": "30 Санса II", "file_id": "CQACAgIAAxkBAANOaFF3qDx-SIfqwr-Fdmpciizd1GkAAo51AALoO5BKByrTYs5PDKU2BA"},
        {"title": "31 Эддард VII", "file_id": "CQACAgIAAxkBAANQaFF3vK2OjlH46v2JoyGTVFKmAQsAAo91AALoO5BKUcv-gOuv02w2BA"},
        {"title": "32 Тирион IV", "file_id": "CQACAgIAAxkBAANSaFF32Q3xOrPvPPoQMCeCjIWeBlwAApB1AALoO5BKAfWgw0Ooz4U2BA"},
        {"title": "33 Арья III", "file_id": "CQACAgIAAxkBAANUaFF38yeE8TMnvhCqbDr-hx5jFi0AApJ1AALoO5BKEE8pKOydcrQ2BA"},
        {"title": "34 Эддард VIII", "file_id": "CQACAgIAAxkBAANWaFF4ByHRBhV_OULxTE43RFIvhLQAApZ1AALoO5BK6_M-BE3W9pA2BA"},
        {"title": "35 Кейтилин VI", "file_id": "CQACAgIAAxkBAANYaFF4HkZ8uWe-me_rPL5CBq16EMUAApd1AALoO5BKWbZ86OpXeQABNgQ"},
        {"title": "36 Эддард IX", "file_id": "CQACAgIAAxkBAANaaFF4PrAaXJiP_dHK-HfQ3t7YIegAApp1AALoO5BKyZHUqw456Yg2BA"},
        {"title": "37 Дейенерис IV", "file_id": "CQACAgIAAxkBAANcaFF4Uh5seAccfPjuXPFQ_vR9odgAAp11AALoO5BKV_5_089BpKg2BA"},
        {"title": "38 Бран V", "file_id": "CQACAgIAAxkBAANeaFF4kuubpQnsftfbFqq9s5ZZDzIAAqF1AALoO5BKIq8khohHay42BA"},
        {"title": "39 Тирион V", "file_id": "CQACAgIAAxkBAANgaFF4qE3X_8NLh4ruJlCDfQU3l4cAAqh1AALoO5BKe3Y9gGGOpEA2BA"},
        {"title": "40 Эддард X", "file_id": "CQACAgIAAxkBAANiaFF4vqUnCt8QBEDy2JLKxPIfhZ8AAql1AALoO5BKSsVOWzSDEAk2BA"},
        {"title": "41 Кейтилин VII", "file_id": "CQACAgIAAxkBAANkaFF40vZYQnXAaMcWBvSJva_EwswAAqx1AALoO5BKg7Sf5cfpbRs2BA"},
        {"title": "42 Джон V", "file_id": "CQACAgIAAxkBAANmaFF46CotFxV3TSl4oTRiObkeifAAAq51AALoO5BKZhwf2_h21ws2BA"},
        {"title": "43 Тирион VI", "file_id": "CQACAgIAAxkBAANoaFF5A9C1EFKWTCOkkOn_ujqfqscAArB1AALoO5BKAXz2FhTb-bw2BA"},
        {"title": "44 Эддард XI", "file_id": "CQACAgIAAxkBAANqaFF5Id6VkzR1N64MP-_2umOufgsAArR1AALoO5BKHZeuFFbYRZY2BA"},
        {"title": "45 Санса III", "file_id": "CQACAgIAAxkBAANsaFF5OyB-pMcqvYzOysTBtFYkChYAArh1AALoO5BK4jUkiuaoYB82BA"},
        {"title": "46 Эддард XII", "file_id": "CQACAgIAAxkBAANuaFF5UQmr0F34LVq3iLxJvYvJj0sAArx1AALoO5BKYqsFEpJi4pM2BA"},
        {"title": "47 Дейенерис V", "file_id": "CQACAgIAAxkBAANwaFF5axFbs9yCTLTdzloG2UrVFRIAAr91AALoO5BKJ9vIwdOnlCY2BA"},
        {"title": "48 Эддард XIII", "file_id": "CQACAgIAAxkBAANyaFF5gHezPLswC9k_xRA0vAeBuPMAAsJ1AALoO5BKVgZO56YL4JA2BA"},
        {"title": "49 Джон VI", "file_id": "CQACAgIAAxkBAAN0aFF5k1bD_UgTx521IrejPfoI0jwAAul7AAItkJBK5l7_SbPc7dM2BA"},
        {"title": "50 Эддард XIV", "file_id": "CQACAgIAAxkBAAN2aFF5piSkSio-huCM4xCrFqQTF0sAAsh1AALoO5BKOIpXuihNXuY2BA"},
        {"title": "51 Арья IV", "file_id": "CQACAgIAAxkBAAN4aFF5vV1xtZX08czbQ2HB01xnDV4AAsp1AALoO5BKA2yoQOTKjn02BA"},
        {"title": "52 Санса IV", "file_id": "CQACAgIAAxkBAAN6aFF52lev_mYinCC401T8-qNDKA4AAs11AALoO5BK3MorTG-hMac2BA"},
        {"title": "53 Джон VII", "file_id": "CQACAgIAAxkBAAN8aFF57sERzBTFflhgBjnEGn9gjloAAtB1AALoO5BKDGejvUSJIgABNgQ"},
        {"title": "54 Бран VI", "file_id": "CQACAgIAAxkBAAN-aFF5_4gcVbKnPHGNNzSoG_2suJgAAtN1AALoO5BKFcCrOmo0KAw2BA"},
        {"title": "55 Дейенерис VI", "file_id": "CQACAgIAAxkBAAOAaFF6FpgEFhAtCsLIgcs_PA8oS70AAtZ1AALoO5BKWO7qO0cRqCk2BA"},
        {"title": "56 Кейтилин VIII", "file_id": "CQACAgIAAxkBAAOCaFF6Kg5EkWHJPhS5_Yvn8Kp7ZToAAtl1AALoO5BK97Acjx64lak2BA"},
        {"title": "57 Тирион VII", "file_id": "CQACAgIAAxkBAAOEaFF6PbC_0te11gg4nvW4doaUPxUAAtt1AALoO5BKqzBWo0i99sM2BA"},
        {"title": "58 Санса V", "file_id": "CQACAgIAAxkBAAOGaFF6U1hn6-Uh12AJm5BDcZyRoAcAAt51AALoO5BKmOH1dloV9NI2BA"},
        {"title": "59 Эддард XV", "file_id": "CQACAgIAAxkBAAOIaFF6cJYcfIbPlOAupVlLgdMrFAUAAjRxAAJwGpBKSKH3obb8XFA2BA"},
        {"title": "60 Кейтилин IX", "file_id": "CQACAgIAAxkBAAOKaFF6hLUnCsyYfYtnH0auyVDzwkMAAuN1AALoO5BK_g-fHY1Gsyg2BA"},
        {"title": "61 Джон VIII", "file_id": "CQACAgIAAxkBAAOMaFF6l5UGfONT_Cyqezirgzxu3NcAAuV1AALoO5BKkSkgzauLNHk2BA"},
        {"title": "62 Дейенерис VII", "file_id": "CQACAgIAAxkBAAOOaFF6qx7FkAsuntfugq2Aw2CiUfgAAuZ1AALoO5BKK68R2tQzf8E2BA"},
        {"title": "63 Тирион VIII", "file_id": "CQACAgIAAxkBAAOQaFF6wXe9p85kdWUVRswfubDRcg0AAuh1AALoO5BKO9EPOezb2ss2BA"},
        {"title": "64 Кейтилин X", "file_id": "CQACAgIAAxkBAAOSaFF60VhsisARfVsNrHmPmjXpI8AAAut1AALoO5BKHAYBex79Mig2BA"},
        {"title": "65 Дейенерис VIII", "file_id": "CQACAgIAAxkBAAOUaFF664GjnBCPeC-7COHGfrMyVAwAAu51AALoO5BKthDwg3GMz342BA"},
        {"title": "66 Арья V", "file_id": "CQACAgIAAxkBAAOWaFF6-8Rcl9Fa5BwJZtRR61hqR8cAAj5xAAJwGpBKZSruHWSNWE42BA"},
        {"title": "67 Бран VII", "file_id": "CQACAgIAAxkBAAOYaFF7FVyBY_ANQMDiTVobOF99FA8AAvJ1AALoO5BK2cxQpStF5LQ2BA"},
        {"title": "68 Санса VI", "file_id": "CQACAgIAAxkBAAOaaFF7MjEQvb27mmunNKFdnnDfopYAAvV1AALoO5BKmkGAImA0SCc2BA"},
        {"title": "69 Дейенерис IX", "file_id": "CQACAgIAAxkBAAOcaFF7Ro2GRUpPHenod17AP04Iq88AAvZ1AALoO5BKAuhWYS2Qpgo2BA"},
        {"title": "70 Тирион IX", "file_id": "CQACAgIAAxkBAAOeaFF7XKGHXJP6GE_-T6dx_Yv_Ts0AApJvAAKC7IlKzcfkaoRS3vQ2BA"},
        {"title": "71 Джон IX", "file_id": "CQACAgIAAxkBAAOgaFF7cDRjTmt1Wp9hK4TvgLqZHf0AAvh1AALoO5BKwxm4qoCthko2BA"},
        {"title": "72 Кейтилин XI", "file_id": "CQACAgIAAxkBAAOiaFF7hQMGKCvPNUQ_L0XJzQjxIwoAAvp1AALoO5BKgJvNocDl9sI2BA"},
        {"title": "73 Дейенерис X", "file_id": "CQACAgIAAxkBAAOkaFF7nn21HA-y-8a7YpyMrPYpbdkAAvt1AALoO5BKHfHF2X2TDtA2BA"},
    ]
    # ----------------------------------------------------------------

    author = session.query(Author).filter_by(name=author_name).first()
    if not author:
        author = Author(name=author_name)
        session.add(author)
        print(f"Добавлен новый автор: {author_name}")

    genre = session.query(Genre).filter_by(name=genre_name).first()
    if not genre:
        genre = Genre(name=genre_name)
        session.add(genre)
        print(f"Добавлен новый жанр: {genre_name}")
    
    existing_book = session.query(Book).filter_by(title=book_title, author=author).first()
    if existing_book:
        print(f"Книга '{book_title}' уже существует в базе. Добавление отменено.")
        return

    new_book = Book(title=book_title, author=author, genre=genre)
    session.add(new_book)
    print(f"Добавлена новая книга: '{book_title}'")
    
    for chapter_data in chapters:
        audio = AudioFile(book=new_book, title=chapter_data["title"], file_id=chapter_data["file_id"])
        session.add(audio)
    
    session.commit()
    print(f"Книга '{book_title}' со всеми главами успешно добавлена в базу данных!")


if __name__ == '__main__':
    add_game_of_thrones()