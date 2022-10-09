class KemonoArtistHandle():

    handles = []

    def __init__(self, handles=None, config=None):
        self.handles = handles

        if config is not None:
            self.handles.append(config.handles)

    def find_more_handles(self, anchors=None):
        """
        pipeline *for artist's ID handle*:  1 - go to artist's pixiv;
                                            2 - get 3 images;
                                            3 - dump them into saucenao;
                                            4 - if saucenao '1xx% founded', get Pixiv artist name as handle;
                                            5 - look for danbooru and/or gelbooru for that image;
                                            6 - get artist romaji name as handle from there too

        pipeline for generic handle: 1 - ?
        """
        # self.handles.append(found_handles)
