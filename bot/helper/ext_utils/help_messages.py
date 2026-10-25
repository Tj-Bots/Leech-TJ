#!/usr/bin/env python3
from bot.helper.telegram_helper.bot_commands import BotCommands

RSS_HELP_MESSAGE = """
<blockquote>➲ <b>Format to adding feed url(s):</b>
Title1 link (required)
Title2 link -c cmd -inf xx -exf xx
Title3 link -c cmd -d ratio:time -z password

➲ <b><i>Argument Details:</i></b>
-c command + any arg
-inf For included words filter.
-exf For excluded words filter.

<b>Example:</b> Title https://www.rss-url.com inf: 1080 or 720 or 144p|mkv or mp4|hevc exf: flv or web|xxx opt: up: mrcc:remote:path/subdir rcf: --buffer-size:8M|key|key:value
This filter will parse links that it's titles contains `(1080 or 720 or 144p) and (mkv or mp4) and hevc` and doesn't conyain (flv or web) and xxx` words. You can add whatever you want.

Another example: inf:  1080  or 720p|.web. or .webrip.|hvec or x264. This will parse titles that contains ( 1080  or 720p) and (.web. or .webrip.) and (hvec or x264). I have added space before and after 1080 to avoid wrong matching. If this `10805695` number in title it will match 1080 if added 1080 without spaces after it.

➲ <b><i>Filter Notes:</i></b>
1. | means and.
2. Add `or` between similar keys, you can add it between qualities or between extensions, so don't add filter like this f: 1080|mp4 or 720|web because this will parse 1080 and (mp4 or 720) and web ... not (1080 and mp4) or (720 and web)."
3. You can add `or` and `|` as much as you want."
4. Take look on title if it has static special character after or before the qualities or extensions or whatever and use them in filter to avoid wrong match.</blockquote>

<b>Timeout:</b> 60 sec.
"""

CATEGORY_HELP_MESSAGE = """Reply to an active /{cmd} which was used to start the download or add gid along with {cmd}
This command mainly for change category incase you decided to change category from already added download.
But you can always use -c or -category with to select category before download start.

<blockquote>➲ <b><i>Upload Custom Drive</i></b>
<code>/{cmd}</code> -id <code>drive_folder_link</code> or <code>drive_id</code> -index <code>https://example.com/0:</code> gid or by replying to active download

<b>NOTE:</b> drive_id must be folder id or folder link and index must be url else it will not accept.
"""

help_string = [f'''⌬ <b><i>Bᴀsɪᴄ Cᴏᴍᴍᴀɴᴅs!</i></b>

<blockquote><b>Use Mirror commands to download your link/file/rcl</b>
╭ /{BotCommands.MirrorCommand[0]} or /{BotCommands.MirrorCommand[1]}: Download via file/url/media to Upload to Cloud Drive.
╰ /{BotCommands.CategorySelect}: Select Custom category to Upload to Cloud Drive from UserTds or Bot Categories.

<b>Use qBit commands for torrents only:</b>
╭ /{BotCommands.QbMirrorCommand[0]} or /{BotCommands.QbMirrorCommand[1]}: Download using qBittorrent and Upload to Cloud Drive.
╰ /{BotCommands.BtSelectCommand}: Select files from torrents by btsel_gid or reply.

<b>Use yt-dlp commands for YouTube or any supported sites:</b>
╰ /{BotCommands.YtdlCommand[0]} or /{BotCommands.YtdlCommand[1]}: Mirror yt-dlp supported link.

<b>Use Leech commands for upload to Telegram:</b>
╭ /{BotCommands.LeechCommand[0]} or /{BotCommands.LeechCommand[1]}: Upload to Telegram.
┊ /{BotCommands.QbLeechCommand[0]} or /{BotCommands.QbLeechCommand[1]}: Download using qBittorrent and upload to Telegram(For torrents only).
╰ /{BotCommands.YtdlLeechCommand[0]} or /{BotCommands.YtdlLeechCommand[1]}: Download using Yt-Dlp(supported link) and upload to telegram.

<b>G-Drive commands:</b>
╭ /{BotCommands.CloneCommand[0]}: Copy file/folder to Cloud Drive.
┊ /{BotCommands.CountCommand} [drive_url]: Count file/folder of Google Drive.
╰ /{BotCommands.DeleteCommand} [drive_url]: Delete file/folder from Google Drive (Only Owner & Sudo).

<b>Cancel Tasks:</b>
╰ /{BotCommands.CancelMirror}: Cancel task by cancel_gid or reply.</blockquote>''',

f'''⌬ <b><i>Usᴇʀs Cᴏᴍᴍᴀɴᴅs!</i></b>

<blockquote><b>Bot Settings:</b>
┊ /{BotCommands.UserSetCommand[0]} or /{BotCommands.UserSetCommand[1]} [query]: Open User Settings (PM also)
╰ /{BotCommands.CoverCommand}: Reply to a video to set your Thumbnail / TMDB poster as its cover

<b>Authentication:</b>
╰ /login: Login to Bot to Access Bot without Temp Pass System (Private)

<b>Bot Stats:</b>
╭ /{BotCommands.StatusCommand[0]} or /{BotCommands.StatusCommand[1]}: Shows a status page of all active tasks. Add <code>me</code> or a user id to see only those tasks.
┊ /{BotCommands.HistoryCommand}: Your last 10 finished tasks with their links.
┊ /{BotCommands.StatsCommand[0]} or /{BotCommands.StatsCommand[1]}: Show Server detailed stats.
╰ /{BotCommands.PingCommand[0]} or /{BotCommands.PingCommand[1]}: Check how long it takes to Ping the Bot.

<b>RSS Feed:</b>
╰ /{BotCommands.RssCommand}: Open RSS Menu (Sub/Unsub/Start/Pause)</blockquote>''',

f'''⌬ <b><i>Oᴡɴᴇʀ ᴏʀ Sᴜᴅᴏs Cᴏᴍᴍᴀɴᴅs!</i></b>

<blockquote><b>Bot Settings:</b>
╭ /{BotCommands.BotSetCommand[0]} or /{BotCommands.BotSetCommand[1]} [query]: Open Bot Settings (Only Owner & Sudo).
╰ /{BotCommands.UsersCommand}: Show User Stats Info (Only Owner & Sudo).

<b>Authentication:</b>
╭ /{BotCommands.AuthorizeCommand[0]} or /{BotCommands.AuthorizeCommand[1]}: Authorize a chat or a user to use the bot (Only Owner & Sudo).
┊ /{BotCommands.UnAuthorizeCommand[0]} or /{BotCommands.UnAuthorizeCommand[1]}: Unauthorize a chat or a user to use the bot (Only Owner & Sudo).
┊ /{BotCommands.AddSudoCommand}: Add sudo user (Only Owner).
┊ /{BotCommands.RmSudoCommand}: Remove sudo users (Only Owner).
┊ /{BotCommands.AddBlackListCommand[0]} or /{BotCommands.AddBlackListCommand[1]}: Add User in BlackListed, so that user can't use the Bot anymore.
╰ /{BotCommands.RmBlackListCommand[0]} or /{BotCommands.RmBlackListCommand[1]}: Remove a BlackListed User, so that user can again use the Bot.

<b>Bot Stats:</b>
╰ /{BotCommands.BroadcastCommand[0]} or /{BotCommands.BroadcastCommand[1]} [reply_msg]: Broadcast to PM users who have started the bot anytime.

<b>G-Drive commands:</b>
╰ /{BotCommands.GDCleanCommand[0]} or /{BotCommands.GDCleanCommand[1]} [drive_id]: Delete all files from specific folder in Google Drive.

<b>Cancel Tasks:</b>
╰ /{BotCommands.CancelAllCommand[0]}: Cancel all Tasks & /{BotCommands.CancelAllCommand[1]} for Multiple Bots.

<b>Maintainance:</b>
╭ /{BotCommands.RestartCommand[0]} or /{BotCommands.RestartCommand[1]}: Restart and Update the Bot (Only Owner & Sudo).
┊ /{BotCommands.RestartCommand[2]}: Restart and Update all Bots (Only Owner & Sudo).
╰ /{BotCommands.LogCommand}: Get a log file of the bot. Handy for getting crash reports (Only Owner & Sudo).

<b>Executors:</b>
╭ /{BotCommands.ShellCommand}: Run shell commands (Only Owner).
┊ /{BotCommands.EvalCommand}: Run Python Code Line | Lines (Only Owner).
┊ /{BotCommands.ExecCommand}: Run Commands In Exec (Only Owner).
┊ /{BotCommands.ClearLocalsCommand}: Clear {BotCommands.EvalCommand} or {BotCommands.ExecCommand} locals (Only Owner).
╰ /exportsession: Generate User StringSession of Same Pyro Version (Only Owner).

<b>RSS Feed:</b>
╰ /{BotCommands.RssCommand}: Open RSS Menu (Sub/Unsub/Start/Pause)

<b>Extras:</b>
╭ /{BotCommands.AddImageCommand} [url/photo]: Add Images in Bot
╰ /{BotCommands.ImagesCommand}: Generate grid of Stored Images.</blockquote>''',

f'''⌬ <b><i>Mɪsᴄᴇʟʟᴀɴᴇᴏᴜs Cᴏᴍᴍᴀɴᴅs!</i></b>

<blockquote><b>Extras:</b>
╭ /{BotCommands.SpeedCommand[0]} or /{BotCommands.SpeedCommand[1]}: Check Speed in VPS/Server.
╰ /{BotCommands.MediaInfoCommand[0]} or /{BotCommands.MediaInfoCommand[1]} [url/media]: Generate MediaInfo of Media or DL Urls

<b>Torrent/Drive Search:</b>
╭ /{BotCommands.ListCommand} [query]: Search in Google Drive(s).
╰ /{BotCommands.SearchCommand} [query]: Search for torrents with API.

<b>Movie/TV Shows/Drama Search:</b>
╭ /{BotCommands.IMDBCommand}: Search in IMDB.
┊ /{BotCommands.AniListCommand}: Search for anime in AniList.
┊ /{BotCommands.AnimeHelpCommand}: Anime help guide.
╰ /{BotCommands.MyDramaListCommand}: Search in MyDramaList.</blockquote>
''']

PASSWORD_ERROR_MESSAGE = """
<blockquote><b>This link requires a password!</b>
- Insert sign <b>::</b> after the link and write the password after the sign.
<b>Example:</b> {}::love you
Note: No spaces between the signs <b>::</b>
For the password, you can use a space!</blockquote>
"""

default_desp = {'AS_DOCUMENT': 'Default type of Telegram file upload. Default is False mean as media.',
                'ANIME_TEMPLATE': 'Set template for AniList Template. HTML Tags supported',
                'AUTHORIZED_CHATS': 'Fill user_id and chat_id of groups/users you want to authorize. Separate them by space.',
                'AUTO_DELETE_MESSAGE_DURATION': "Interval of time (in seconds), after which the bot deletes it's message and command message which is expected to be viewed instantly.\n\n <b>NOTE:</b> Set to -1 to disable auto message deletion.",
                'BASE_URL': 'Valid BASE URL where the bot is deployed to use torrent web files selection. Format of URL should be http://myip, where myip is the IP/Domain(public) of your bot or if you have chosen port other than 80 so write it in this format http://myip:port (http and not https). Str',
                'BASE_URL_PORT': 'Which is the BASE_URL Port. Default is 80. Int',
                'BLACKLIST_USERS': 'Restrict User from Using the Bot. It will Display a BlackListed Msg. USER_ID separated by space. Str',
                'BOT_MAX_TASKS': 'Maximum number of Task Bot will Run parallel. (Queue Tasks Included). Int',
                'STORAGE_THRESHOLD': 'To leave specific storage free and any download will lead to leave free storage less than this value will be cancelled the default unit is GB. Int',
                'LEECH_LIMIT':  'To limit the Torrent/Direct/ytdlp leech size. the default unit is GB. Int',
                'CLONE_LIMIT': 'To limit the size of Google Drive folder/file which you can clone. the default unit is GB. Int',
                'MEGA_LIMIT': 'To limit the size of Mega download. the default unit is GB. Int',
                'TORRENT_LIMIT': 'To limit the size of torrent download. the default unit is GB. Int',
                'DIRECT_LIMIT': 'To limit the size of direct link download. the default unit is GB. Int',
                'YTDLP_LIMIT': 'To limit the size of ytdlp download. the default unit is GB. Int',
                'PLAYLIST_LIMIT': 'To limit Maximum Playlist Number. Int',
                'IMAGES': 'Add multiple telgraph(graph.org) image links that are seperated by spaces.',
                'IMG_SEARCH': 'Put Keyword to Download Images. Sperarte each name by , like anime, iron man, god of war',
                'IMG_PAGE': 'Set the page value for downloading a image. Each page have approx 70 images. Deafult is 1. Int',
                'IMDB_TEMPLATE': 'Set Bot Default IMDB Template. HTML Tags, Emojis supported. str',
                'AUTHOR_NAME': 'Author name for Telegraph pages, Shown in Telegraph Page as by AUTHOR_NAME',
                'AUTHOR_URL': 'Author URL for Telegraph page, Put Channel URL to Show Join Channel. Str',
                'COVER_IMAGE': 'Cover Image for Telegraph Photo Link',
                'TITLE_NAME': 'Title name for Telegraph pages (while using /list command)',
                'GD_INFO': 'Description of file uploaded to gdrive using bot',
                'DELETE_LINKS': 'Delete TgLink/Magnet/File on Start of Task to Auto Clean Group. Default is False',
                'EXCEP_CHATS': 'Exception Chats which will not use Logging, chat_id separated by space. Str',
                'SAFE_MODE': 'Hide Task Name, Source Link and Indexing of Leech Link for Safety Precautions. Default is False',
                'SOURCE_LINK': 'Add a Extra Button of Source Link whether it is Magnet Link or File Link or DL Link. Default is False',
                'SHOW_EXTRA_CMDS': 'Add Extra Commands beside Arg Format for -z or -e. \n\n<b>COMMANDS: </b> /unzipxxx or /zipxxx or /uzx or /zx',
                'BOT_THEME': 'Theme of the Bot to Switch. For now Deafault Theme Availabe is minimal. You can make your own Theme and Add in BSet. \n\n<b>Sample Format</b>: https://t.ly/9rVXq',
                'USER_MAX_TASKS': 'Limit the Maximum task for users of group at a time. use the Int',
                'DAILY_TASK_LIMIT': 'Maximum task a user can do in one day. use the Int',
                'DISABLE_DRIVE_LINK': 'Disable drive link button. Default is False. Bool',
                'DAILY_MIRROR_LIMIT': 'Total size upto which user can Mirror in one day. the default unit is GB. Int',
                'GDRIVE_LIMIT': 'To limit the size of Google Drive folder/file link for leech, Zip, Unzip. the default unit is GB. Int',
                'DAILY_LEECH_LIMIT': 'Total size upto which user can Leech in one day. the default unit is GB. Int',
                'USER_TASKS_LIMIT': 'The maximum limit on every users for all tasks. Int',
                'FSUB_IDS': 'Fill chat_id(-100xxxxxx) of groups/channel you want to force subscribe. Separate them by space. Int\n\nNote: Bot should be added in the filled chat_id as admin',
                'BOT_PM': 'File/links send to the BOT PM also. Default is False',
                'BOT_TOKEN': 'The Telegram Bot Token that you got from @BotFather',
                'CMD_SUFFIX': 'Telegram Bot Command Index number or Custom Text. This will added at the end all commands except Global Commands. Str',
                'DATABASE_URL': "Your Mongo Database URL (Connection string). Follow this Generate Database to generate database. Data will be saved in Database: auth and sudo users, users settings including thumbnails for each user, rss data and incomplete tasks.\n\n <b>NOTE:</b> You can always edit all settings that saved in database from the official site -> (Browse collections)",
                'DEFAULT_UPLOAD': 'Whether rc to upload to RCLONE_PATH or gd to upload to GDRIVE_ID or ddl to upload to DDLserver. Default is gd.',
                'DOWNLOAD_DIR': 'The path to the local folder where the downloads should be downloaded to. ',
                'MDL_TEMPLATE': 'Set Bot Custom Default MyDramaList Template. HTML Tags, Emojis Supported',
                'CLEAN_LOG_MSG': 'Clean Leech Log & Bot PM Task Start Message. Default is False',
                'LEECH_LOG_ID': "Chat ID to where leeched files would be uploaded. Int. NOTE: Only available for superGroup/channel. Add -100 before channel/superGroup id. In short don't add bot id or your id!",
                'MIRROR_LOG_ID': "Chat ID to where Mirror files would be Send. Int. NOTE: Only available for superGroup/channel. Add -100 before channel/superGroup id. In short don't add bot id or your id!. For Multiple id Separate them by space.",
                'EQUAL_SPLITS': 'Split files larger than LEECH_SPLIT_SIZE into equal parts size (Not working with zip cmd). Default is False.',
                'EXTENSION_FILTER': "File extensions that won't upload/clone. Separate them by space.",
                'GDRIVE_ID': 'This is the Folder/TeamDrive ID of the Google Drive OR root to which you want to upload all the mirrors using google-api-python-client.',
                'INCOMPLETE_TASK_NOTIFIER': 'Get incomplete task messages after restart. Require database and superGroup. Default is False',
                'INDEX_URL': 'Refer to https://gitlab.com/ParveenBhadooOfficial/Google-Drive-Index.',
                'IS_TEAM_DRIVE': 'Set True if uploading to TeamDrive using google-api-python-client. Default is False',
                'SHOW_MEDIAINFO': 'Add Button to Show MediaInfo in Leeched file. Bool',
                'SCREENSHOTS_MODE': 'Enable or Diable generating Screenshots via -ss arg. Default is False. Bool',
                'CAP_FONT': 'Add Custom Caption Font to Leeched Files, Available Values : b, i, u, s, code, spoiler. Reset Var to use Regular ( No Format )',
                'LEECH_FILENAME_PREFIX': 'Add custom word prefix to leeched file name. Str',
                'LEECH_FILENAME_SUFFIX': 'Add custom word suffix to leeched file name. Str',
                'LEECH_FILENAME_CAPTION': 'Add custom word caption to leeched file/vedios. Str',
                'LEECH_FILENAME_REMNAME': 'Remove custom word from the leeched file name. Str',
                'LOGIN_PASS': 'Permanent pass for user to skip the token system',
                'TOKEN_TIMEOUT': 'Token timeout for each group member in sec. Int',
                'DEBRID_LINK_API': 'Set debrid-link.com API for 172 Supported Hosters Leeching Support. Str',
                'REAL_DEBRID_API': 'Set real-debrid.com API for Torrent Cache & Few Supported Hosters (VPN Maybe). Str',
                'LEECH_SPLIT_SIZE': 'Size of split in bytes. Default is 2GB. Default is 4GB if your account is premium.',
                'MEDIA_GROUP': 'View Uploaded splitted file parts in media group. Default is False.',
                'MEGA_EMAIL': 'E-Mail used to sign-in on mega.nz for using premium account. Str',
                'MEGA_PASSWORD': 'Password for mega.nz account. Str',
                'OWNER_ID': 'The Telegram User ID (not username) of the Owner of the bot.',
                'QUEUE_ALL': 'Number of parallel tasks of downloads and uploads. For example if 20 task added and QUEUE_ALL is 8, then the summation of uploading and downloading tasks are 8 and the rest in queue. Int. NOTE: if you want to fill QUEUE_DOWNLOAD or QUEUE_UPLOAD, then QUEUE_ALL value must be greater than or equal to the greatest one and less than or equal to summation of QUEUE_UPLOAD and QUEUE_DOWNLOAD',
                'QUEUE_DOWNLOAD': 'Number of all parallel downloading tasks. Int',
                'QUEUE_UPLOAD': 'Number of all parallel uploading tasks. Int',
                'RCLONE_FLAGS': 'key:value|key|key|key:value . Check here all RcloneFlags.',
                'RCLONE_PATH': "Default rclone path to which you want to upload all the mirrors using rclone.",
                'RCLONE_SERVE_URL': 'Valid URL where the bot is deployed to use rclone serve. Format of URL should be http://myip, where myip is the IP/Domain(public) of your bot or if you have chosen port other than 80 so write it in this format http://myip:port (http and not https)',
                'RCLONE_SERVE_USER': 'Username for rclone serve authentication.',
                'RCLONE_SERVE_PASS': 'Password for rclone serve authentication.',
                'RCLONE_SERVE_PORT': 'Which is the RCLONE_SERVE_URL Port. Default is 8080.',
                'RSS_CHAT_ID': 'Chat ID where rss links will be sent. If you want message to be sent to the channel then add channel id. Add -100 before channel id. Int',
                'RSS_DELAY': 'Time in seconds for rss refresh interval. Recommended 900 second at least. Default is 900 in sec. Int',
                'SEARCH_API_LINK': 'Search api app link. Get your api from deploying this repository. Supported Sites: 1337x, Piratebay, Nyaasi, Torlock, Torrent Galaxy, Zooqle, Kickass, Bitsearch, MagnetDL, Libgen, YTS, Limetorrent, TorrentFunk, Glodls, TorrentProject and YourBittorrent',
                'SEARCH_LIMIT': 'Search limit for search api, limit for each site and not overall result limit. Default is zero (Default api limit for each site).',
                'SEARCH_PLUGINS': 'List of qBittorrent search plugins (github raw links). I have added some plugins, you can remove/add plugins as you want.',
                'STATUS_LIMIT': 'Limit the no. of tasks shown in status message with buttons. Default is 10. NOTE: Recommended limit is 4 tasks.',
                'STATUS_UPDATE_INTERVAL': 'Time in seconds after which the progress/status message will be updated. Recommended 10 seconds at least.',
                'STOP_DUPLICATE': "Bot will check file/folder name in Drive incase uploading to GDRIVE_ID. If it's present in Drive then downloading or cloning will be stopped. (NOTE: Item will be checked using name and not hash, so this feature is not perfect yet). Default is False",
                'SUDO_USERS': 'Fill user_id of users whom you want to give sudo permission. Separate them by space. Int',
                'TELEGRAM_API': 'This is to authenticate your Telegram account for downloading Telegram files. You can get this from https://my.telegram.org.',
                'TELEGRAM_HASH': 'This is to authenticate your Telegram account for downloading Telegram files. You can get this from https://my.telegram.org.',
                'TIMEZONE': 'Set your Preferred Time Zone for Restart Message. Get yours at <a href="http://www.timezoneconverter.com/cgi-bin/findzone.tzc">Here</a> Str',
                'TORRENT_TIMEOUT': 'Timeout of dead torrents downloading with qBittorrent and Aria2c in seconds. Int',
                'UPSTREAM_REPO': "Your github repository link, if your repo is private add https://username:{githubtoken}@github.com/{username}/{reponame} format. Get token from Github settings. So you can update your bot from filled repository on each restart.",
                'UPSTREAM_BRANCH': 'Upstream branch for update. Default is master.',
                'UPGRADE_PACKAGES': 'Install New Requirements File without thinking of Crash. Bool',
                'SAVE_MSG': 'Add button of save message. Bool',
                'SET_COMMANDS': 'Set bot command automatically. Bool',
                'JIODRIVE_TOKEN': 'Set token for the jiodrive.xyz to download the files. str',
                'USER_TD_MODE': 'Enable User GDrive TD to Use. Default is False',
                'USER_TD_SA': 'Add Global SA mail for User to give Permissions to Bot for UserTD Upload. Like wzmlx@googlegroups.com. Str',
                'COVER_DUMP': "Save /cover results also in LEECH_LOG_ID (dump chat). When False the video goes only to the user's PM. Default is False.",
                'MEDIA_STORE': "Default for Media Store: every leeched file gets a Store Link, anyone who opens it gets the file from the bot in PM. Users can change it for themselves in User Settings. Default is False.",
                'VT_CUSTOM_CMDS': "Extra tools for the Video Tools menu (-vt), one per line as <code>name: ffmpeg args</code>, same format as FFmpeg Cmds in User Settings. Example: <code>compress: -i mltb.video -c:v libx265 -crf 28 -c:a copy mltb.mkv</code>. Every name becomes a button.",
                'PM_ACCESS': "Let everyone use the bot in private chat, it works like in authorized groups. Blacklisted users stay blocked. Default is False.",
                'RICH_MESSAGES': "Send the status message as a Telegram Rich Message: Cancel / Select buttons inside every task and lines between tasks, instead of /cancel commands. Needs the wzgram library. Default is False.",
                'DISABLE_FF_MODE': "Disable FFmpeg Cmds (-ff) for all users. When True the option is hidden from User Settings. Default is False.",
                'TMDB_ACCESS_TOKEN': "TMDB API Key or Read Access Token, used for Auto Thumbnail (movie/series poster) in User Settings. Get it from https://www.themoviedb.org/settings/api",
                'HELPER_TOKENS': "Extra bot tokens for Hyper download/upload, separated by space. Add all of them as admins in LEECH_LOG_ID chat.\n\n<b>NOTE:</b> Restart required.",
                'HELPER_STRINGS': "Extra user session strings for Hyper download/upload, separated by space. Premium accounts are the fastest. Add all of them to LEECH_LOG_ID chat.\n\n<b>NOTE:</b> Restart required.",
                'USE_HYPER': "Use Hyper (parallel multi client) download and upload for Telegram files. Works with HELPER_TOKENS, HELPER_STRINGS or USER_SESSION_STRING. Default is True.",
                'HYPER_THREADS': "Number of parallel parts per Hyper download. 0 means auto by clients count.",
                'HYPER_CHUNK': "Chunk size in bytes for every Hyper request. 0 means 262144 (256KB). Minimum is 65536.",
                'HYPER_PIPELINE': "Requests in flight per Hyper download. 0 means 32.",
                'USER_SESSION_STRING': "To download/upload from your telegram account and to send rss. To generate session string use this command <code>python3 generate_string_session.py</code> after mounting repo folder for sure.\n\n<b>NOTE:</b> You can't use bot with private message. Use it with superGroup.",
                'USE_SERVICE_ACCOUNTS': 'Whether to use Service Accounts or not, with google-api-python-client. For this to work see Using Service Accounts section below. Default is False',
                'WEB_PINCODE': ' Whether to ask for pincode before selecting files from torrent in web or not. Default is False. Bool.',
                'YT_DLP_OPTIONS': 'Default yt-dlp options. Check all possible options HERE or use this script to convert cli arguments to api options. Format: key:value|key:value|key:value. Add ^ before integer or float, some numbers must be numeric and some string. \nExample: "format:bv*+mergeall[vcodec=none]|nocheckcertificate:True"'
                }

_ARGS = {
    "name": (
        "New Name",
        """㊂ <b>New Name</b> » <code>-n</code>

<blockquote>Rename the file or folder before upload.
➲ <code>/cmd link -n My Movie 2024.mkv</code></blockquote>
<i>Not for torrents with many files. Your Prefix / Suffix / Remname from /us are still applied.</i>""",
    ),
    "yt_name": (
        "New Name",
        """㊂ <b>New Name</b> » <code>-n</code>

<blockquote>Rename the downloaded file.
➲ <code>/cmd link -n My Video</code></blockquote>
<i>Don't add the extension, yt-dlp adds it by itself.</i>""",
    ),
    "zip": (
        "Extract / Zip",
        """㊂ <b>Extract / Zip</b> » <code>-e</code> <code>-z</code>

<blockquote>➲ <code>/cmd link -e</code> extract the archive
➲ <code>/cmd link -e pass123</code> extract with password
➲ <code>/cmd link -z</code> zip the files
➲ <code>/cmd link -z pass123</code> zip with password
➲ <code>/cmd link -e -z</code> extract, then zip again</blockquote>
<i>When both are used it always extracts first.</i>""",
    ),
    "yt_zip": (
        "Zip",
        """㊂ <b>Zip</b> » <code>-z</code>

<blockquote>➲ <code>/cmd link -z</code> zip the files
➲ <code>/cmd link -z pass123</code> zip with password</blockquote>
<i>Useful for playlists, you get one archive.</i>""",
    ),
    "upload": (
        "Upload To",
        """㊂ <b>Upload To</b> » <code>-up</code>

<blockquote>Choose where the files go. Without it the bot uses the default upload.
➲ <code>/cmd link -up gd</code> Google Drive
➲ <code>/cmd link -up rc</code> your RClone Path
➲ <code>/cmd link -up ddl</code> your DDL Servers (GoFile, PixelDrain...)
➲ <code>/cmd link -up rcl</code> pick remote and folder with buttons
➲ <code>/cmd link -up remote:folder</code> direct rclone path
➲ <code>/cmd link -up mrcc:remote:folder</code> with your own rclone.conf
➲ <code>/cmd link -up movies</code> an Upload Path saved in /us</blockquote>
<i>Set DDL Servers, RClone and Upload Paths in /us → Mirror.</i>""",
    ),
    "dump": (
        "Dump Chat",
        """㊂ <b>Dump Chat</b> » <code>-ud</code>

<blockquote>Send the files to a chat or channel instead of here.
➲ <code>/cmd link -ud MyChannel</code> a Leech Dump saved in /us
➲ <code>/cmd link -ud -100123456789</code> chat id
➲ <code>/cmd link -ud @mychannel</code> username
➲ <code>/cmd link -ud all</code> all of your Leech Dumps</blockquote>
<i>The bot must be admin there. With more than one dump and no <code>-ud</code>, you get buttons.</i>""",
    ),
    "multi": (
        "Multi Links",
        """㊂ <b>Multi Links</b> » <code>-i</code>

<blockquote>Run several links/files in a row. Reply to the <b>first</b> one:
➲ <code>/cmd -i 5</code> this message and the next 4</blockquote>
<i>Each one runs as a separate task.</i>""",
    ),
    "samedir": (
        "Same Folder",
        """㊂ <b>Same Folder</b> » <code>-m</code>

<blockquote>Put the files of multi or bulk links in one folder.
➲ <code>/cmd -i 5 -m Season 1</code>
➲ <code>/cmd -b -m Season 1</code></blockquote>
<i>Good with <code>-z</code> to get one archive of everything.</i>""",
    ),
    "bulk": (
        "Bulk",
        """㊂ <b>Bulk</b> » <code>-b</code>

<blockquote>Reply to a message or a .txt file with one link per line:
<code>link1 -n first name</code>
<code>link2 -z</code>
<code>link3 -e</code>
Then reply to it with <code>/cmd -b</code>
➲ <code>/cmd -b 3:8</code> only links 3 to 8
➲ <code>/cmd -b :10</code> first 10 links</blockquote>
<i>Args for each link go on its own line.</i>""",
    ),
    "join": (
        "Join Parts",
        """㊂ <b>Join Parts</b> » <code>-j</code>

<blockquote>Join split files (.001 .002 ...) back to one file.
➲ <code>/cmd link -j</code> link with split files
➲ <code>/cmd -i 3 -j -m folder</code> parts sent as 3 messages</blockquote>
<i>Runs before extract and zip.</i>""",
    ),
    "select": (
        "Select Files",
        """㊂ <b>Select Files</b> » <code>-s</code>

<blockquote>Choose which files of a torrent to download.
➲ <code>/cmd magnet -s</code></blockquote>
<i>You get a button to open the file list.</i>""",
    ),
    "yt_select": (
        "Quality",
        """㊂ <b>Quality</b> » <code>-s</code>

<blockquote>Always show the quality buttons, even if a default format is set in your YT-DLP Options.
➲ <code>/cmd link -s</code></blockquote>""",
    ),
    "seed": (
        "Seed",
        """㊂ <b>Seed</b> » <code>-d</code>

<blockquote>Keep seeding the torrent after upload.
➲ <code>/cmd magnet -d</code> default ratio and time
➲ <code>/cmd magnet -d 1.5:60</code> ratio 1.5 or 60 minutes
➲ <code>/cmd magnet -d 2</code> only ratio
➲ <code>/cmd magnet -d :30</code> only time</blockquote>""",
    ),
    "auth": (
        "Login",
        """㊂ <b>Login</b> » <code>-u</code> <code>-p</code>

<blockquote>For direct links or indexes that need a username and password.
➲ <code>/cmd link -u user -p pass</code></blockquote>""",
    ),
    "headers": (
        "Headers",
        """㊂ <b>Headers</b> » <code>-h</code>

<blockquote>Add custom headers to a direct link.
➲ <code>/cmd link -h Referer: https://site.com Cookie: a=b</code></blockquote>""",
    ),
    "rcf": (
        "RClone Flags",
        """㊂ <b>RClone Flags</b> » <code>-rcf</code>

<blockquote>Extra rclone flags for this task, separated by <code>|</code>
➲ <code>/cmd link -up rc -rcf --buffer-size:8M|--drive-starred-only</code></blockquote>
<i>Overrides your RClone Flags from /us. All flags: <a href='https://rclone.org/flags/'>rclone.org/flags</a></i>""",
    ),
    "drive": (
        "Drive Folder",
        """㊂ <b>Drive Folder</b> » <code>-id</code> <code>-index</code>

<blockquote>Upload to a specific Google Drive folder.
➲ <code>/cmd link -id folder_link</code>
➲ <code>/cmd link -id folder_id -index https://index.site/0:</code></blockquote>""",
    ),
    "category": (
        "Category",
        """㊂ <b>Category</b> » <code>-c</code>

<blockquote>Upload to a Drive category by name (bot categories or your User TDs).
➲ <code>/cmd link -c Movies</code></blockquote>
<i>Without it, you get buttons when there is more than one.</i>""",
    ),
    "screenshots": (
        "Screenshots",
        """㊂ <b>Screenshots</b> » <code>-ss</code>

<blockquote>Send screenshots of every video with the upload.
➲ <code>/cmd link -ss 6</code></blockquote>
<i>To always get them, set Screenshots / Sample Video in /us → Leech.</i>""",
    ),
    "thumb": (
        "Thumbnail",
        """㊂ <b>Thumbnail</b> » <code>-t</code>

<blockquote>Use another thumbnail only for this task.
➲ <code>/cmd link -t https://site.com/image.jpg</code>
➲ <code>/cmd link -t https://t.me/channel/123</code> image from Telegram</blockquote>
<i>Your thumbnail from /us and Auto Thumbnail are used when this is not set.</i>""",
    ),
    "convert": (
        "Convert Media",
        """㊂ <b>Convert Media</b> » <code>-ca</code> <code>-cv</code>

<blockquote>➲ <code>/cmd link -cv mp4</code> all videos to mp4
➲ <code>/cmd link -ca mp3</code> all audios to mp3
➲ <code>/cmd link -ca mp3 -cv mp4</code> both
➲ <code>/cmd link -ca mp3 + flac ogg</code> only flac and ogg to mp3
➲ <code>/cmd link -cv mkv - webm flv</code> all videos to mkv except webm and flv</blockquote>
<i>Videos change format without re-encoding when possible, so it's fast. Original files are replaced.</i>""",
    ),
    "split": (
        "Split Size",
        """㊂ <b>Split Size</b> » <code>-sp</code>

<blockquote>Split size only for this task, your setting in /us stays.
➲ <code>/cmd link -sp 1.5GB</code>
➲ <code>/cmd link -sp 500MB</code></blockquote>
<i>Max is 2GB, or 4GB with a premium user session.</i>""",
    ),
    "video_tools": (
        "Video Tools",
        """㊂ <b>Video Tools</b> » <code>-vt</code>

<blockquote>Opens a menu before the task starts. Pick tools, then Continue:
➲ Rename · Video + Video · Video + Audio · Video + Subtitle
➲ Extract · Remove Stream · Trim · Screenshots · Convert To</blockquote>
<i>Everything is copied, nothing is re-encoded, so it's fast. The owner can add more tools.</i>""",
    ),
    "extract_audio": (
        "Extract Audio",
        """㊂ <b>Extract Audio</b> » <code>-ea</code>

<blockquote>Take the audio out of every video and upload only the audio.
➲ <code>/cmd link -ea</code> as mp3
➲ <code>/cmd link -ea m4a</code> as m4a (fastest, mostly without re-encoding)
➲ <code>/cmd link -ea flac</code> also <code>opus</code> <code>ogg</code> <code>wav</code></blockquote>
<i>Videos without audio stay as they are.</i>""",
    ),
    "ffmpeg": (
        "FFmpeg Cmds",
        """㊂ <b>FFmpeg Cmds</b> » <code>-ff</code>

<blockquote>Run an FFmpeg command you saved in /us → Universal → FFmpeg Cmds.
➲ <code>/cmd link -ff tomp3</code>
In the saved command write <code>mltb</code> as the input and output name.
The input decides which files it runs on:
<code>mltb</code> all files · <code>mltb.video</code> all videos · <code>mltb.audio</code> all audios · <code>mltb.mkv</code> only mkv
<code>tomp3: -i mltb.audio -c:a libmp3lame mltb.mp3</code>
➲ <code>/cmd link -ff tomp3 subs</code> run more than one</blockquote>""",
    ),
    "rclone_dl": (
        "From RClone",
        """㊂ <b>From RClone</b>

<blockquote>Download from your cloud like a link.
➲ <code>/cmd rcl</code> pick the file with buttons
➲ <code>/cmd remote:folder/file.mkv</code>
➲ <code>/cmd mrcc:remote:folder</code> with your own rclone.conf</blockquote>""",
    ),
    "tg": (
        "Telegram Links",
        """㊂ <b>Telegram Links</b>

<blockquote>Reply to a file, or send a message link:
➲ <code>/cmd https://t.me/channel/123</code> public
➲ <code>/cmd https://t.me/c/123456/78</code> private
➲ <code>/cmd -i 5</code> reply to the first file to take 5 in a row</blockquote>
<i>Private chats need your User Session (/us) or the bot's.</i>""",
    ),
    "yt_opt": (
        "YT-DLP Options",
        """㊂ <b>YT-DLP Options</b> » <code>-opt</code>

<blockquote>Extra yt-dlp options for this task, separated by <code>|</code>
➲ <code>/cmd link -opt playliststart:^5|playlistend:^10</code>
➲ <code>/cmd link -opt writesubtitles:true|format:bv*+ba</code>
Add <code>^</code> before numbers.</blockquote>
<i>Save options you always use in /us → Universal. Cookies too.</i>""",
    ),
    "clone_links": (
        "Supported",
        """㊂ <b>Supported</b>

<blockquote>➲ <code>/cmd gdrive_link</code>
➲ GDTot · Filepress · Filebee · Appdrive · GDFlix links
➲ <code>/cmd remote:folder -up remote2:folder</code> rclone to rclone</blockquote>""",
    ),
    "clone_up": (
        "Upload To",
        """㊂ <b>Upload To</b> » <code>-up</code>

<blockquote>For rclone paths, choose where to copy.
➲ <code>/cmd remote:folder -up rcl</code> pick with buttons
➲ <code>/cmd remote:folder -up remote2:folder</code></blockquote>
<i>Without it your RClone Path is used.</i>""",
    ),
}

_EXAMPLES = {
    "name": "/cmd link -n My Movie 2024.mkv",
    "yt_name": "/cmd link -n My Video",
    "zip": "/cmd link -e -z pass123",
    "yt_zip": "/cmd link -z",
    "upload": "/cmd link -up ddl",
    "dump": "/cmd link -ud all",
    "multi": "/cmd -i 5",
    "samedir": "/cmd -i 5 -m Season 1",
    "bulk": "/cmd -b",
    "join": "/cmd link -j",
    "select": "/cmd magnet -s",
    "yt_select": "/cmd link -s",
    "seed": "/cmd magnet -d 1.5:60",
    "auth": "/cmd link -u user -p pass",
    "headers": "/cmd link -h Referer: https://site.com",
    "rcf": "/cmd link -up rc -rcf --buffer-size:8M",
    "drive": "/cmd link -id folder_link",
    "category": "/cmd link -c Movies",
    "screenshots": "/cmd link -ss 6",
    "thumb": "/cmd link -t https://site.com/image.jpg",
    "convert": "/cmd link -ca mp3 -cv mp4",
    "ffmpeg": "/cmd link -ff tomp3",
    "extract_audio": "/cmd link -ea mp3",
    "video_tools": "/cmd link -vt",
    "split": "/cmd link -sp 1.5GB",
    "rclone_dl": "/cmd rcl",
    "tg": "/cmd https://t.me/channel/123",
    "yt_opt": "/cmd link -opt playliststart:^5|playlistend:^10",
    "clone_links": "/cmd gdrive_link",
    "clone_up": "/cmd remote:folder -up rcl",
}

_MAIN = {
    "leech": """㊂ <b>Leech</b>

<blockquote>Download anything and upload it to Telegram.
➲ <code>/cmd link</code>
➲ Reply to a link or file with <code>/cmd</code></blockquote>
<blockquote>Direct links · Telegram files · Torrents · GDrive · Mega · RClone and more.
Your settings from /us are used: thumbnail, caption, transfer mode, dumps...</blockquote>
<i>Tap an arg to see how to use it:</i>""",
    "mirror": """㊂ <b>Mirror</b>

<blockquote>Download anything and upload it to GDrive, RClone or DDL.
➲ <code>/cmd link</code>
➲ Reply to a link or file with <code>/cmd</code></blockquote>
<blockquote>Direct links · Telegram files · Torrents · GDrive · Mega · RClone and more.
You get the links in a message when it's done.</blockquote>
<i>Tap an arg to see how to use it:</i>""",
    "qbleech": """㊂ <b>qBittorrent Leech</b>

<blockquote>Download torrents with qBittorrent and upload to Telegram.
➲ <code>/cmd magnet</code>
➲ Reply to a .torrent file with <code>/cmd</code></blockquote>
<i>Tap an arg to see how to use it:</i>""",
    "qbmirror": """㊂ <b>qBittorrent Mirror</b>

<blockquote>Download torrents with qBittorrent and upload to GDrive, RClone or DDL.
➲ <code>/cmd magnet</code>
➲ Reply to a .torrent file with <code>/cmd</code></blockquote>
<i>Tap an arg to see how to use it:</i>""",
    "ytleech": """㊂ <b>YT-DLP Leech</b>

<blockquote>Download from YouTube and 1000+ sites and upload to Telegram.
➲ <code>/cmd link</code>
You choose the quality with buttons.</blockquote>
<i>Tap an arg to see how to use it:</i>""",
    "ytmirror": """㊂ <b>YT-DLP Mirror</b>

<blockquote>Download from YouTube and 1000+ sites and upload to GDrive, RClone or DDL.
➲ <code>/cmd link</code>
You choose the quality with buttons.</blockquote>
<i>Tap an arg to see how to use it:</i>""",
    "clone": """㊂ <b>Clone</b>

<blockquote>Copy files between clouds without downloading them.
➲ <code>/cmd link</code>
➲ Reply to a link with <code>/cmd</code></blockquote>
<i>Tap an arg to see how to use it:</i>""",
}

_MENUS = {
    "leech": ["name", "zip", "dump", "multi", "samedir", "bulk", "join", "select",
              "seed", "auth", "headers", "screenshots", "thumb", "split", "convert", "extract_audio", "video_tools", "ffmpeg",
              "rclone_dl", "tg"],
    "mirror": ["name", "zip", "upload", "multi", "samedir", "bulk", "join", "select",
               "seed", "auth", "headers", "rcf", "drive", "category", "convert",
               "extract_audio", "video_tools", "ffmpeg", "rclone_dl", "tg"],
    "qbleech": ["name", "zip", "dump", "select", "seed", "multi", "samedir", "bulk",
                "screenshots", "thumb", "split", "convert", "extract_audio", "video_tools", "ffmpeg"],
    "qbmirror": ["name", "zip", "upload", "select", "seed", "multi", "samedir", "bulk",
                 "rcf", "drive", "category", "convert", "extract_audio", "video_tools", "ffmpeg"],
    "ytleech": ["yt_name", "yt_select", "yt_opt", "yt_zip", "dump", "multi", "samedir",
                "bulk", "screenshots", "thumb", "split", "convert", "extract_audio", "video_tools", "ffmpeg"],
    "ytmirror": ["yt_name", "yt_select", "yt_opt", "yt_zip", "upload", "multi",
                 "samedir", "bulk", "rcf", "drive", "category", "convert", "extract_audio", "video_tools", "ffmpeg"],
    "clone": ["clone_links", "clone_up", "multi", "rcf", "drive", "category"],
}


def _menu_type(key, cmd):
    if key == "CLONE":
        return "clone"
    leech = cmd in (
        BotCommands.LeechCommand
        + BotCommands.QbLeechCommand
        + BotCommands.YtdlLeechCommand
    )
    kind = "leech" if leech else "mirror"
    if key == "YT":
        return f"yt{kind}"
    if cmd in BotCommands.QbLeechCommand + BotCommands.QbMirrorCommand:
        return f"qb{kind}"
    return kind


def help_menu(key, user_id, cmd, page=0, item=None):
    from bot.helper.telegram_helper.button_build import ButtonMaker

    cmd = cmd.lstrip("/").split("@")[0]
    mtype = _menu_type(key, cmd)
    names = _MENUS[mtype]
    base = f"wzmlx {user_id} help {key} {cmd}"
    buttons = ButtonMaker()
    if item is not None and 0 <= item < len(names):
        text = _ARGS[names[item]][1]
        if example := _EXAMPLES.get(names[item]):
            text += f"\n\n<b>Example:</b> <code>{example}</code>"
        buttons.ibutton("Bᴀᴄᴋ", f"{base} p {page}")
        buttons.ibutton("Cʟᴏsᴇ", f"wzmlx {user_id} close")
        return text.replace("/cmd", f"/{cmd}"), buttons.build_menu(2)
    per_page = 8
    pages = max(1, -(-len(names) // per_page))
    page = min(max(page, 0), pages - 1)
    for i in range(page * per_page, min((page + 1) * per_page, len(names))):
        buttons.ibutton(_ARGS[names[i]][0], f"{base} i {i} {page}")
    if pages > 1:
        if page > 0:
            buttons.ibutton("⫷", f"{base} p {page - 1}", "l_body")
        buttons.ibutton(f"{page + 1}/{pages}", f"{base} p {page}", "l_body")
        if page < pages - 1:
            buttons.ibutton("⫸", f"{base} p {page + 1}", "l_body")
    buttons.ibutton("Cʟᴏsᴇ", f"wzmlx {user_id} close", "footer")
    return _MAIN[mtype].replace("/cmd", f"/{cmd}"), buttons.build_menu(2, lb_cols=3)
