import music_tag
import requests
from mutagen import id3
from pathlib import Path
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import Picture
from base64 import b64encode

class AudioTagger:
    
    def __init__(self):
        pass

    def set_audio_tags(self, fullpath, artists=None, artist_array=None, name=None, album_name=None, release_year=None,
                       disc_number=None, track_number=None, track_id_str=None, album_artist=None, image_url=None):
        """sets music_tag metadata using mutagen if possible"""
        
        album_artist = album_artist or artists  # Use artists if album_artist is None

        extension = str(fullpath).split('.')[-1]

        if extension == 'mp3':
            self._set_mp3_tags(fullpath, artists, name, album_name, release_year, disc_number,
                               track_number, track_id_str, album_artist, image_url)
        else:
            self._set_other_tags(fullpath, artists, artist_array, album_artist, name, album_name, release_year, disc_number,
                                 track_number, track_id_str, image_url)

    def _set_mp3_tags(self, fullpath, artist, name, album_name, release_year, disc_number, 
                      track_number, track_id_str, album_artist, image_url):
        tags = id3.ID3(fullpath)

        mp3_map = {
            "TPE1": artist,
            "TIT2": name,
            "TALB": album_name,
            "TDRC": release_year,
            "TDOR": release_year,
            "TPOS": str(disc_number) if disc_number else None,
            "TRCK": str(track_number) if track_number else None,
            "COMM": "https://open.spotify.com/track/" + track_id_str if track_id_str else None,
            "TPE2": album_artist,
        }

        for tag, value in mp3_map.items():
            if value:
                tags[tag] = id3.Frames[tag](encoding=3, text=value)

        if image_url:
            albumart = requests.get(image_url).content
            if albumart:
                tags["APIC"] = id3.APIC(encoding=3, mime="image/jpeg", type=3, desc="0", data=albumart)

        tags.save()

    def _set_other_tags(self, fullpath, artist, artist_array, album_artist, name, album_name, release_year, disc_number, 
                        track_number, track_id_str, image_url):

        """ Try to save dummy artist once to avoid corrupt header
            idk wtf is going on here
            See: https://github.com/quodlibet/mutagen/issues/591 """
            
        tags = OggVorbis(fullpath)
        tags["artist"] = "AAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        try:
            tags.save(padding=lambda info: 0)
        except mutagen.oggvorbis.OggVorbisHeaderError:
            pass
        
        other_map = {
            #"artist": ['dummy artist'],
            #"artist": artist_array,
            #"album_artist": album_artist,
            #"tracktitle": name,
            #"album": album_name,
            #"year": release_year,
            #"discnumber": str(disc_number) if disc_number else None,
            #"tracknumber": str(track_number),
            #"comment": f"id[spotify.com:track:{track_id_str}]" if track_id_str else None
        }

        tags2 = OggVorbis(fullpath)
        tags2["artist"] = artist_array
        tags2["album_artist"] = album_artist
        tags2["title"] = name
        tags2["album"] = album_name
        tags2["year"] = release_year
        tags2["discnumber"] = str(disc_number) if disc_number else None
        tags2["tracknumber"] = str(track_number)
        tags2["comment"] = f"id[spotify.com:track:{track_id_str}]" if track_id_str else None
        #except:
        #    print("WTF IS GOING ON")
        tags2.save(padding=lambda info: 0)

        if image_url:
            albumart = requests.get(image_url).content
            cover_path = f"{Path(fullpath).parent.resolve()}/cover.jpg"

            with open(f"{Path(fullpath).parent.resolve()}/cover.jpg", mode="wb") as cover_file:
                print(f"Saving cover to {cover_path}")
                cover_file.write(albumart)
            if albumart:
                covart = Picture()
                covart.data = albumart
                covart.type = 3  # Cover (front)
                print("Embedding cover image")
                tags2['metadata_block_picture'] = b64encode(covart.write()).decode('ascii')
                #audio.save()
        try:
            tags2.save(padding=lambda info: 0)
        except:
            print("[META] Cover art caused metadata resizing issue")