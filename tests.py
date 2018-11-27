# python packages
import os
import csv
import json
import unittest
import pandas as pd

# project files
import index_lyrics
import label_lyrics


class TestETL(unittest.TestCase):

    test_txt = 'test.txt'
    input_csv = 'test_input.csv'
    output_csv = 'test_output.csv'

    def tearDown(self):
        if os.path.exists(self.test_txt):
            os.remove(self.test_txt)
        if os.path.exists(self.input_csv):
            os.remove(self.input_csv)
        if os.path.exists(self.output_csv):
            os.remove(self.output_csv)

    def test_read_file_contents(self):
        # txt
        expected_contents = ('hello\nworld\n123', 'default')
        with open(self.test_txt, 'w') as f:
            f.write(expected_contents[0])
        actual_contents = index_lyrics.read_file_contents(self.test_txt)
        self.assertEqual(expected_contents, actual_contents)
        # json
        expected_contents = ({'hello': 'world', '1': {'2': '3', '4': '5'}}, 'default')
        with open(self.test_txt, 'w') as f:
            json.dump(expected_contents[0], f)
        actual_contents = index_lyrics.read_file_contents(self.test_txt, read_json=True)
        self.assertEqual(expected_contents, actual_contents)

    def test_add_col_if_dne(self):
        data = {'a': ['b', 'c'], 'd': ['e', 'f']}
        df = pd.DataFrame(data)
        expected_df = pd.DataFrame({'a': ['b', 'c'], 'd': ['e', 'f'], 'g': ['h', 'h']})
        actual_df = index_lyrics.add_col_if_dne(df, 'g', 'h')  # should be added
        actual_df = index_lyrics.add_col_if_dne(df, 'a', 'b')  # should not be added
        self.assertEqual(expected_df.to_dict(), actual_df.to_dict())

    def test_index_lyrics(self):
        with open(self.input_csv, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['msd_artist', 'msd_title'])
            writer.writerow(['10cc', "I'm not in love"])
        # test 1: vanilla input csv with no additional columns
        index_lyrics.index_lyrics(self.input_csv, self.output_csv)
        expected_rows = [
            ['msd_artist', 'msd_title', 'is_english', 'lyrics_available', 'wordcount', 'lyrics_filename'],
            ['10cc', "I'm not in love", '1', '1', '218', '10cc___Im_not_in_love'],
        ]
        with open(self.output_csv, 'r') as f:
            reader = csv.reader(f)
            for index, actual_row in enumerate(reader):
                self.assertEqual(expected_rows[index], actual_row)
        # test 2: already proccessed csv as output -- should be the same
        index_lyrics.index_lyrics(self.output_csv, self.output_csv)
        with open(self.output_csv, 'r') as f:
            reader = csv.reader(f)
            for index, actual_row in enumerate(reader):
                self.assertEqual(expected_rows[index], actual_row)
        # test 3: input csv with mixed processed & unprocessed rows -- should process remaining rows
        with open(self.output_csv, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(['10cc', "woman in love", '0', '-1', '-1', 'aaa'])
            writer.writerow(['10cc', "The things we do for love", '-1', '-1', '111', ''])
            writer.writerow(['apple', "orange", '-1', '-1', 'aaa', ''])
        expected_rows.append(['10cc', "woman in love", '1', '1', '300', '10cc___woman_in_love'])
        expected_rows.append(['10cc', "The things we do for love", '1', '1', '286', '10cc___The_things_we_do_for_love'])
        expected_rows.append(['apple', "orange", '0', '0', '0', 'apple___orange'])
        index_lyrics.index_lyrics(self.output_csv, self.output_csv)
        with open(self.output_csv, 'r') as f:
            reader = csv.reader(f)
            for index, actual_row in enumerate(reader):
                self.assertEqual(expected_rows[index], actual_row)

                
class TestLabelLyrics(unittest.TestCase):

    def test_match_song_tags_to_mood_expanded(self):
        """
        Uses the moods "aggression", "angst", "brooding" to validate that
        expanded mood matching works as expected
        
        For reference, these moods were pasted in on 11/26/18
            "aggression": [
                ["aggression", "aggressive"],
                ["aggress"],
                ["not so aggressive"]
            ],
            "angst": [
                ["angst", "anxiety", "anxious", "jumpy", "nervous", "angsty"],
                ["angst", "anxiety", "anxious", "jumpy", "nervous", "angsty"],
                ["gangst", "langstrumpf", "farangstar", "gaaangstaa", "klangstark"]
            ],
            "brooding": [
                ["brooding", "contemplative", "meditative", "reflective"],
                ["brood", "contemplat", "meditat", "reflect"],
                ["broodcast", "marilyn manson - the reflecting god", "silverchair-reflections of a sound"]
            ],
        """
        tags = list()
        # should match aggressive 2
        tags += ['aggressiiiiive', 'not so aggressive', 'not so aggressss']
        # should match angst 2
        tags += ['jumpy', 'nervou', 'nervous', 'gangst', 'langstrumpf']
        # should match brooding 3
        tags += ['marilyn manson', 'broodccast', 'broodcast', 'contemplative', 'meditation']
        expected_mood = 'brooding'
        expected_scoreboard = dict.fromkeys(label_lyrics.MOOD_CATEGORIES_EXPANDED.keys(), 0)
        expected_scoreboard['aggression'] = 2
        expected_scoreboard['angst'] = 2
        expected_scoreboard['brooding'] = 3
        actual_mood, actual_scoreboard = label_lyrics.match_song_tags_to_mood_expanded(pd.Series(tags))
        self.assertEqual(expected_mood, actual_mood)
        self.assertEqual(expected_scoreboard, actual_scoreboard)
        
        
if __name__ == '__main__':
    unittest.main()