# with Love @LazyDeveloperr 💘
# Subscribe YT @LazyDeveloperr - to learn more about this for free...

import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import asyncio
import json
import os
import shutil
import time
from pyrogram import enums
from datetime import datetime
from info import *
from Script import script
from plugins.rlazy_thumbnail import *
logging.getLogger("pyrogram").setLevel(logging.WARNING)
from pyrogram.types import InputMediaPhoto
from database.lazy_utils import progress_for_pyrogram, humanbytes
from database.users_chats_db import db
from lazybot.ran_text import random_char

async def youtube_dl_call_back(client, query):
    cb_data = query.data
    cb_data = query.data
    # youtube_dl extractors
    lzmsg = query.message.reply_to_message  # msg will be callback query
    message_idx = lzmsg.id #getting id
    print(f"{message_idx}")
    # youtube_dl extractors
    tg_send_type, youtube_dl_format, youtube_dl_ext, ranom = cb_data.split("|")
    print(cb_data)
    random1 = random_char(5)
    
    save_ytdl_json_path = DOWNLOAD_LOCATION + \
        "/" + str(query.from_user.id) + f'{ranom}' + ".json"
    try:
        with open(save_ytdl_json_path, "r", encoding="utf8") as f:
            response_json = json.load(f)
    except (FileNotFoundError) as e:
        await client.delete_messages(
            chat_id=query.message.chat.id,
            message_ids=message_idx,
            revoke=True
        )
        return False
    youtube_dl_url = query.message.reply_to_message.text
    custom_file_name = str(response_json.get("title")) + \
        "_" + youtube_dl_format + "." + youtube_dl_ext
    youtube_dl_username = None
    youtube_dl_password = None
    if "|" in youtube_dl_url:
        url_parts = youtube_dl_url.split("|")
        if len(url_parts) == 2:
            youtube_dl_url = url_parts[0]
            custom_file_name = url_parts[1]
        elif len(url_parts) == 4:
            youtube_dl_url = url_parts[0]
            custom_file_name = url_parts[1]
            youtube_dl_username = url_parts[2]
            youtube_dl_password = url_parts[3]
        else:
            for entity in query.message.reply_to_message.entities:
                if entity.type == "text_link":
                    youtube_dl_url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    l = entity.length
                    youtube_dl_url = youtube_dl_url[o:o + l]
        if youtube_dl_url is not None:
            youtube_dl_url = youtube_dl_url.strip()
        if custom_file_name is not None:
            custom_file_name = custom_file_name.strip()
        # https://stackoverflow.com/a/761825/4723940
        if youtube_dl_username is not None:
            youtube_dl_username = youtube_dl_username.strip()
        if youtube_dl_password is not None:
            youtube_dl_password = youtube_dl_password.strip()
        logger.info(youtube_dl_url)
        logger.info(custom_file_name)
    else:
        for entity in query.message.reply_to_message.entities:
            if entity.type == "text_link":
                youtube_dl_url = entity.url
            elif entity.type == "url":
                o = entity.offset
                l = entity.length
                youtube_dl_url = youtube_dl_url[o:o + l]
    await query.edit_message_text(
        text=script.DOWNLOAD_START,
    )
    description = script.CUSTOM_CAPTION_UL_FILE
    if "fulltitle" in response_json:
        description = response_json["fulltitle"][0:1021]
        # escape Markdown and special characters
    tmp_directory_for_each_user = DOWNLOAD_LOCATION + "/" + str(query.from_user.id) + f'{random1}'
    if not os.path.isdir(tmp_directory_for_each_user):
        os.makedirs(tmp_directory_for_each_user)
    download_directory = tmp_directory_for_each_user + "/" + custom_file_name
    command_to_exec = []
    if tg_send_type == "audio":
        command_to_exec = [
            "yt-dlp",
            "-c",
            "--max-filesize", str(TG_MAX_FILE_SIZE),
            "--prefer-ffmpeg",
            "--extract-audio",
            "--audio-format", youtube_dl_ext,
            "--audio-quality", youtube_dl_format,
            youtube_dl_url,
            "-o", download_directory
        ]
    else:
        # command_to_exec = ["youtube-dl", "-f", youtube_dl_format, "--hls-prefer-ffmpeg", "--recode-video", "mp4", "-k", youtube_dl_url, "-o", download_directory]
        minus_f_format = youtube_dl_format
        if "youtu" in youtube_dl_url:
            minus_f_format = youtube_dl_format + "+bestaudio"
        command_to_exec = [
            "yt-dlp",
            "-c",
            "--max-filesize", str(TG_MAX_FILE_SIZE),
            "--embed-subs",
            "-f", minus_f_format,
            "--hls-prefer-ffmpeg", youtube_dl_url,
            "-o", download_directory
        ]
    if HTTP_PROXY != "":
        command_to_exec.append("--proxy")
        command_to_exec.append(HTTP_PROXY)
    if youtube_dl_username is not None:
        command_to_exec.append("--username")
        command_to_exec.append(youtube_dl_username)
    if youtube_dl_password is not None:
        command_to_exec.append("--password")
        command_to_exec.append(youtube_dl_password)
    command_to_exec.append("--no-warnings")
    # command_to_exec.append("--quiet")
    logger.info(command_to_exec)
    start = datetime.now()
    process = await asyncio.create_subprocess_exec(
        *command_to_exec,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    logger.info(e_response)
    logger.info(t_response)
    ad_string_to_replace = "please report this issue on https://yt-dl.org/bug . Make sure you are using the latest version; see  https://yt-dl.org/update  on how to update. Be sure to call youtube-dl with the --verbose flag and include its complete output."
    if e_response and ad_string_to_replace in e_response:
        error_message = e_response.replace(ad_string_to_replace, "")
        await query.edit_message_text(
            text=error_message
        )
        return False

    if t_response:
        logger.info(t_response)
        try:
            os.remove(save_ytdl_json_path)
        except FileNotFoundError as exc:
            pass
        
        end_one = datetime.now()
        time_taken_for_download = (end_one -start).seconds
        file_size = TG_MAX_FILE_SIZE + 1
        try:
            file_size = os.stat(download_directory).st_size
        except FileNotFoundError as exc:
            download_directory = os.path.splitext(download_directory)[0] + "." + "mkv"
            # https://stackoverflow.com/a/678242/4723940
            file_size = os.stat(download_directory).st_size
        if file_size > TG_MAX_FILE_SIZE:
            await bot.edit_message_text(
                text=script.RCHD_TG_API_LIMIT.format(time_taken_for_download, humanbytes(file_size)),
            )
        else:
            is_w_f = False
            '''images = await generate_screen_shots(
                download_directory,
                tmp_directory_for_each_user,
                is_w_f,
                DEF_WATER_MARK_FILE,
                300,
                9
            )
            logger.info(images)'''
            await query.edit_message_text(
                text=script.UPLOAD_START,
            )

            start_time = time.time()
            if (await db.get_upload_as_doc(query.from_user.id)) is False:
                thumbnail = await Gthumb01(client, query)
                await client.send_document(
                    chat_id=query.message.chat.id,
                    document=download_directory,
                    thumb=thumbnail,
                    caption=description,
                    reply_to_message_id=message_idx,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        script.UPLOAD_START,
                        query.message,
                        start_time
                    )
                )
            else:
                 width, height, duration = await Mdata01(download_directory)
                 thumb_image_path = await Gthumb02(client, query, duration, download_directory)
                 await client.send_video(
                    chat_id=query.message.chat.id,
                    video=download_directory,
                    caption=description,
                    duration=duration,
                    width=width,
                    height=height,
                    supports_streaming=True,
                    thumb=thumb_image_path,
                    reply_to_message_id=message_idx,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        script.UPLOAD_START,
                        query.message,
                        start_time
                    )
                )
            if tg_send_type == "audio":
                duration = await Mdata03(download_directory)
                thumbnail = await Gthumb01(client, query)
                await client.send_audio(
                    chat_id=query.message.chat.id,
                    audio=download_directory,
                    caption=description,
                    parse_mode=enums.ParseMode.HTML,
                    duration=duration,
                    thumb=thumbnail,
                    reply_to_message_id=message_idx,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        script.UPLOAD_START,
                        query.message,
                        start_time
                    )
                )
            elif tg_send_type == "vm":
                width, duration = await Mdata02(download_directory)
                thumbnail = await Gthumb02(client, query, duration, download_directory)
                await client.send_video_note(
                    chat_id=query.message.chat.id,
                    video_note=download_directory,
                    duration=duration,
                    length=width,
                    thumb=thumbnail,
                    reply_to_message_id=message_idx,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        script.UPLOAD_START,
                        query.message,
                        start_time
                    )
                )
            else:
                logger.info("Did this happen? :\\")
            end_two = datetime.now()
            time_taken_for_upload = (end_two - end_one).seconds
            try:
                shutil.rmtree(tmp_directory_for_each_user)
                os.remove(thumbnail)
            except:
                pass
            await query.edit_message_text(
                text=script.AFTER_SUCCESSFUL_UPLOAD_MSG_WITH_TS.format(time_taken_for_download, time_taken_for_upload),
                disable_web_page_preview=True
            )
