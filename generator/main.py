import json
import sys
import traceback
from time import time
from typing import Any

from alive_progress import alive_bar  # type: ignore
from const import (KAIZE_EMAIL, KAIZE_PASSWORD, KAIZE_SESSION,
                   KAIZE_XSRF_TOKEN, attribution, pprint)
from combiner import combine_anitrakt, combine_arm, combine_fribb
from converter import (link_kaize_to_mal, link_otakotaku_to_mal,
                       link_silveryasha_to_mal)
from dumper import update_attribution, update_markdown
from fetcher import (get_anime_offline_database, get_anitrakt, get_arm,
                     get_fribb_animelists, simplify_aod_data,
                     simplify_silveryasha_data)
from kaize import Kaize
from otakotaku import OtakOtaku
from prettyprint import Platform, Status
from utils import check_git_any_changes

if (KAIZE_XSRF_TOKEN is None) and (KAIZE_SESSION is None) and (KAIZE_EMAIL is None) and (KAIZE_PASSWORD is None):
    raise Exception('Kaize login info does not available in environment variables')


def main() -> None:
    """Main function"""
    try:
        start_time = time()
        pprint.print(Platform.SYSTEM, Status.READY, "Generator ready to use")
        aod = get_anime_offline_database()
        aod_arr = simplify_aod_data(aod)
        kza = Kaize(
            session=KAIZE_SESSION,
            email=KAIZE_EMAIL,
            password=KAIZE_PASSWORD,
            xsrf_token=KAIZE_XSRF_TOKEN).get_anime()
        ota = OtakOtaku().get_anime()
        sy_ = simplify_silveryasha_data()
        arm = get_arm()
        anitrakt = get_anitrakt()
        fribb = get_fribb_animelists()
        git_changes = check_git_any_changes()
        if git_changes is True:
            pprint.print(Platform.SYSTEM, Status.INFO, "Build database")
            pprint.print(Platform.KAIZE, Status.BUILD,
                         "Linking Kaize slug to MyAnimeList ID by fuzzy matching")
            aod_arr = link_kaize_to_mal(kza, aod_arr)
            pprint.print(Platform.OTAKOTAKU, Status.BUILD,
                         "Linking Otak Otaku ID to MyAnimeList ID by fuzzy matching")
            aod_arr = link_otakotaku_to_mal(ota, aod_arr)
            pprint.print(Platform.SILVERYASHA, Status.BUILD,
                         "Linking SilverYasha ID to MyAnimeList ID by fuzzy matching")
            aod_arr = link_silveryasha_to_mal(sy_, aod_arr)
            pprint.print(Platform.ARM, Status.BUILD,
                         "Combining ARM data with AOD data")
            aod_arr = combine_arm(arm, aod_arr)
            pprint.print(Platform.ANITRAKT, Status.BUILD,
                         "Combining AniTrakt data with AOD data")
            aod_arr = combine_anitrakt(anitrakt, aod_arr)
            pprint.print(Platform.FRIBB, Status.BUILD,
                         "Combining Fribb's Animelists data with AOD data")
            aod_arr = combine_fribb(fribb, aod_arr)
            final_arr: list[dict[str, Any]] = []
            with alive_bar(len(aod_arr),
                           title="Fixing missing keys",
                           spinner=None) as bar:  # type: ignore
                for item in aod_arr:
                    data = {
                        "title": item.get("title", None),
                        "anidb": item.get("anidb", None),
                        "anilist": item.get("anilist", None),
                        "animeplanet": item.get("animeplanet", None),
                        "anisearch": item.get("anisearch", None),
                        "annict": item.get("annict", None),
                        "imdb": item.get("imdb", None),
                        "kaize": item.get("kaize", None),
                        "kaize_id": item.get("kaize_id", None),
                        "kitsu": item.get("kitsu", None),
                        "livechart": item.get("livechart", None),
                        "myanimelist": item.get("myanimelist", None),
                        "notify": item.get("notify", None),
                        "otakotaku": item.get("otakotaku", None),
                        "shikimori": item.get("shikimori", None),
                        "shoboi": item.get("shoboi", None),
                        "silveryasha": item.get("silveryasha", None),
                        "themoviedb": item.get("themoviedb", None),
                        # "themoviedb_type": item.get("themoviedb_type", None),
                        # "themoviedb_season": item.get("themoviedb_season", None),
                        "trakt": item.get("trakt", None),
                        "trakt_type": item.get("trakt_type", None),
                        "trakt_season": item.get("trakt_season", None),
                    }
                    final_arr.append(data)
                    bar()
            with open("database/animeapi.json", "w", encoding="utf-8") as file:
                json.dump(final_arr, file)
        else:
            # get data from animeapi.json
            with open("database/animeapi.json", "r", encoding="utf-8") as file:
                final_arr = json.load(file)
        attr = update_attribution(final_arr, attribution)
        attr = update_markdown(attr=attr)
        counts: dict[str, int] = attr["counts"]  # type: ignore
        print(f"""Data parsed:
* aniDB: {counts["anidb"]}
* AniList: {counts["anilist"]}
* Anime-Planet: {counts["animeplanet"]}
* aniSearch: {counts["anisearch"]}
* Annict: {counts["annict"]}
* IMDb: {counts["imdb"]}
* Kaize: {counts["kaize"]}
* Kitsu: {counts["kitsu"]}
* LiveChart.me: {counts["livechart"]}
* MyAnimeList: {counts["myanimelist"]}
* Notify.moe: {counts["notify"]}
* Otak-Otaku: {counts["otakotaku"]}
* Shikimori: {counts["shikimori"]}
* Shoboi: {counts["shoboi"]}
* SilverYasha: {counts["silveryasha"]}
* The Movie DB: {counts["themoviedb"]}
* Trakt: {counts["trakt"]}
""")
        end_time = time()
        pprint.print(
            Platform.SYSTEM,
            Status.INFO,
            f"Generator finished in {end_time - start_time:.2f} seconds",
        )
    except KeyboardInterrupt:
        print()
        pprint.print(Platform.SYSTEM, Status.ERR, "Stopped by user")
    except Exception as err:
        print()
        pprint.print(Platform.SYSTEM, Status.ERR, f"Error: {err}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        pprint.print(Platform.SYSTEM, Status.INFO, "Exiting...")
        sys.exit(0)
