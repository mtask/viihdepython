#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import cli
import elisaviihde
import simpsonitorgparser
from datetime import datetime
from user_input import get_input



def main():
    parser = cli.init_argparser()
    parser.add_argument('-f', '--folder_name', help='Elisa Viihde Simpsonit folder name')
    parser.add_argument('-s', '--season_prefix', help='prefix for season folder name')
    params = parser.parse_args()

    username = cli.read_input(params.user, 'Elisa Viihde Username')
    password = cli.read_password(params.passfile, 'Elisa Viihde Password')

    e = elisaviihde.Elisaviihde()
    if not e.login(username, password):
        return

    folder_name = cli.read_input(params.folder_name,
                                 'Elisa Viihde Simpsonit folder name [Simpsonit]',
                                 u'Simpsonit')
    season_folder_name = cli.read_input(params.season_prefix,
                                        'prefix for season folder name or "None" [Season ]',
                                        u'Season ')
    if season_folder_name == 'None':
        season_folder_name = u''

    simpsonit_folder = e.find_folder_by_name(folder_name)
    if simpsonit_folder is None:
        print('Folder', folder_name, 'not found')
        return
    
    episodes = simpsonitorgparser.parse_schedule()
    simpsonit_folder_id = simpsonit_folder['id']
    root_simponit_recordings = e.recordings(simpsonit_folder_id)
    
    to_be_moved = []  # list of (recording, episode) pairs
    for recording in root_simponit_recordings:
        episode = find_episode(episodes, recording)
        if episode:
            to_be_moved.append((recording, episode))
    print('Found', len(to_be_moved), 'episodes to be moved')

    answer = get_input("Enter 'y' to continue, anything else to cancel: ")
    if answer == 'y':
        for move in to_be_moved:
            recording = move[0]
            episode = move[1]
            target_folder = e.find_or_create_subfolder(season_folder_name + str(episode['season']),
                                                       simpsonit_folder_id)
            try:
                status = e.move(recording['programId'], target_folder['id'])
            except TypeError:
                print("Failed to move", recording['programId'])
                continue
            print('MOVED:', status, recording['startTime'], episode['name'], 'to', target_folder['name'])
        print("Moving done.")
    else:
        print("Moving canceled.")
        
    
def find_episode(episodes, recording):
    result = []
    recording_dt = datetime.strptime(recording['startTime'], "%d.%m.%Y %H.%M")
    for episode in episodes:
        if recording['name'].startswith('Simpsonit') and episode['datetime'] == recording_dt:
            result.append(episode)
    
    if len(result) > 1:
        print('SKIPPED: found more than 1 episodes for', recording['startTime'], result)
    elif len(result) == 1:
        episode = result[0]
        print('MATCH:', recording['startTime'], episode['datetime'], episode['name'], '->', 'Season', episode['season'])
        return episode
    else:
        print('SKIPPED: found 0 episodes for', recording['startTime'])

if __name__ == '__main__':
    main()
