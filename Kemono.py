import KemonoConfig
import KemonoSpider
import KemonoArtistHandle


def main():

    config = KemonoConfig.KemonoConfig()
    config.parse_arguments()
    config.parse_configfile(override=config.arguments)

    artist = KemonoArtistHandle.KemonoArtistHandle(config=config)
    if config.find_more_handles:
        artist.find_more_handles()

    spider = KemonoSpider.KemonoSpider(artist, config)

    # artist_links = get_artist_links(driver, _config.handles)

    # for link in artist_links:
    #     download_artist(driver, link)

    # driver.quit()


if __name__ == "__main__":
    main()

"""
TODO:   - implement most important optional arguments (-f, -i, -b & -B);
        - implement log (& debug?);
        - refactor and modulate code.

        - V2:   - database for artists' files and cards;
                - kemonoparty artists monitor;
                - interface between PixivUtils2 & Kemono (skip images if same as downloaded by PU2, etc);
                - unify PU2 and Kemono.
        
        - V3:   - Multithreading (+multiple drivers) [refactor 2.0];
                - Finetuning of -f, -b, -B & cards' content/links
                - implement remaining optional arguments
"""
