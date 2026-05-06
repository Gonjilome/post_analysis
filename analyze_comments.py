import glob
import json
import os
import sys
import numpy as np
import re
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

safety_keywords = ['safe', 'danger', 'risk', 'careful', 'rescue', 'drown', 'hospital', 'hurt', 'caution', ' die', ' rip ']
negative_keyphrases = {(r'^don ', 'dont ', 'don\'t ', 'do not ', 'tourist'): [(' come', ' com', r'^go', ' go ', 'cme'), (' want', ' wan', ' wnt'), (' here', 'her ', 'hre '), (' no ', r'^no'), ('away')], 
                       ('ruining', 'ruin ', 'ruined', 'go away'): ['']}

def safe_mean(data):

    print(data)
    return np.nan_to_num(np.mean(data), nan=-1)

posts = {'ig':[], 'fb':[], 'tt':[]}

for key in posts.keys():
    for caption_path, comment_path in zip(glob.glob(os.path.join(key + '/caption', '*.json')), glob.glob(os.path.join(key + '/comments', '*.json'))):

        id = caption_path.split('\\')[1].split('_')[0]

        with open(caption_path, 'r', encoding='utf-8') as f:
            caption = json.load(f)

        with open(comment_path, 'r', encoding='utf-8') as f:
            
            comments = []
            for c in json.load(f):
                comments.append(c)
            
            comments = list(set(comments))  # Keep only unique comments

        posts[key].append({'post_id': id, 'caption': caption, 'comments': comments})

all_comments = [comment 
                for posts in posts.values() 
                for post in posts 
                for comment in post.get("comments", [])]


post_stats = {'ig':{}, 'fb':{}, 'tt':{}, 'overall':{}}

for key in posts.keys():

    comment_count = []
    captions = []

    for post in posts.get(key):

        comments = post.get('comments')
        comment_count.append(len(comments))
        
        if any(safe_key in post.get('caption') for safe_key in safety_keywords):
            post.update({'safety_caption': True})
        else:
            post.update({'safety_caption': False})

        caption_hashtags = re.findall(r'#\w+', post.get('caption'))
        hashtags = caption_hashtags + [match for comment in comments for match in re.findall(r'#\w+', comment)]
        tagged_comments = [match for comment in comments for match in re.findall(r'@', comment)]

        post.update({'hashtags': hashtags})
        post.update({'tagged_comments': len(tagged_comments)})

        negative_comments = []
        for comment in comments:
            negative = False

            # Each keyword is paired with an operative main_key, like some variation of "don't." "come" or "go" is only negative if "don't" is also there.
            for main_key in negative_keyphrases.keys():

                if any(keyword in comment for keyword in main_key):
                    for secondary_keysets in negative_keyphrases.get(main_key):

                        for keyset in secondary_keysets:
                            if any(keyword in comment for keyword in keyset):

                                negative = True
                                break

            if negative:

                negative_comments.append(comment)

        # print(negative_comments)

        post.update({'negative_comments': len(negative_comments)})

    post_stats[key].update({'post_count': len(comment_count)})
    post_stats[key].update({'comment_count': int(np.sum(comment_count))})
    post_stats[key].update({'comments_mean': float(safe_mean(comment_count))})
    post_stats[key].update({'tags_count': int(np.sum([post['tagged_comments'] for post in posts[key]]))})
    post_stats[key].update({'tags_mean': float(safe_mean([post['tagged_comments'] for post in posts[key]]))})

    post_stats[key].update({'tags_per_comment_mean': float(safe_mean([(post['tagged_comments'] / len(post['comments'])) 
                                                                    if len(post['comments']) > 0 else 0 
                                                                    for post in posts[key]]))})
    
    post_stats[key].update({'negative_count': int(np.sum([post['negative_comments'] for post in posts[key]]))})
    post_stats[key].update({'negative_mean': float(safe_mean([post['negative_comments'] for post in posts[key]]))})
    post_stats[key].update({'negative_per_comment_mean': float(safe_mean([(post['negative_comments'] / len(post['comments'])) 
                                                                if len(post['comments']) > 0 else 0 
                                                                for post in posts[key]]))})

    safe_captions = [post['caption'] for post in posts[key] if post['safety_caption']]
    unsafe_captions = [post['caption'] for post in posts[key] if not post['safety_caption']]

    post_stats[key].update({'safe_caption_count': len(safe_captions)})
    post_stats[key].update({'unsafe_caption_count': len(unsafe_captions)})

    safe_posts = [post for post in posts[key] if post['safety_caption']]
    unsafe_posts = [post for post in posts[key] if not post['safety_caption']]

    safe_post_comments = [post['comments'] for post in safe_posts]
    unsafe_post_comments = [post['comments'] for post in unsafe_posts]
    safe_post_comment_counts = [len(c) for c in safe_post_comments]
    unsafe_post_comment_counts = [len(c) for c in unsafe_post_comments]

    post_stats[key].update({'safe_post_tags_count': int(np.sum([post['tagged_comments'] for post in safe_posts]))})
    post_stats[key].update({'unsafe_post_tags_count': int(np.sum([post['tagged_comments'] for post in unsafe_posts]))})

    post_stats[key].update({'tags_per_comment_safe_mean': float(safe_mean([(post['tagged_comments'] / len(post['comments'])) 
                                                                    if len(post['comments']) > 0 else 0 
                                                                    for post in safe_posts]))})
    
    post_stats[key].update({'tags_per_comment_unsafe_mean': float(safe_mean([(post['tagged_comments'] / len(post['comments'])) 
                                                                    if len(post['comments']) > 0 else 0 
                                                                    for post in unsafe_posts]))})

    post_stats[key].update({'safe_post_comment_count': int(np.sum(safe_post_comment_counts))})
    post_stats[key].update({'unsafe_post_comment_count': int(np.sum(unsafe_post_comment_counts))})
    post_stats[key].update({'safe_post_comments_mean': float(safe_mean(safe_post_comment_counts))})
    post_stats[key].update({'unsafe_post_comments_mean': float(safe_mean(unsafe_post_comment_counts))})

    hashtag_counted = dict(Counter([hashtag for post in posts[key] for hashtag in post['hashtags']]))
    hashtag_sorted = dict(sorted(hashtag_counted.items(), key=lambda item: item[1], reverse=True))
    top_hashtags = {k: hashtag_sorted[k] for k in list(hashtag_sorted)[:10]}
    post_stats[key].update({'top_hashtags': top_hashtags})

    safe_post_comments_abt_safety = []
    for post in safe_posts:

        safe_comments = [comment for comment in post['comments'] if any(safe_key in comment for safe_key in safety_keywords)]
        safe_post_comments_abt_safety.append(safe_comments)
    
    safe_post_comments_abt_safety_count = [len(c) for c in safe_post_comments_abt_safety]

    unsafe_post_comments_abt_safety = []
    for post in unsafe_posts:

        safe_comments = [comment for comment in post['comments'] if any(safe_key in comment for safe_key in safety_keywords)]
        unsafe_post_comments_abt_safety.append(safe_comments)
    
    unsafe_post_comments_abt_safety_count = [len(c) for c in unsafe_post_comments_abt_safety]

    # print(safe_post_comments_abt_safety_count)
    # print(unsafe_post_comments_abt_safety_count)

    safe_valid_indices = np.nonzero(np.array(safe_post_comment_counts))
    safe_post_comments_abt_safety_per_comment = (np.array(safe_post_comments_abt_safety_count)[safe_valid_indices] / 
                                                   np.array(safe_post_comment_counts)[safe_valid_indices])
    
    safe_post_comments_abt_safety_per_comment_mean = float(safe_mean(safe_post_comments_abt_safety_per_comment))

    unsafe_valid_indices = np.nonzero(np.array(unsafe_post_comment_counts))
    unsafe_post_comments_abt_safety_per_comment = (np.array(unsafe_post_comments_abt_safety_count)[unsafe_valid_indices] / 
                                                   np.array(unsafe_post_comment_counts)[unsafe_valid_indices])
    
    unsafe_post_comments_abt_safety_per_comment_mean = float(safe_mean(unsafe_post_comments_abt_safety_per_comment))

    safe_post_comments_abt_safety_per_comment_ratios = list(zip((np.array(safe_post_comments_abt_safety_count)).tolist(), 
                                                                (np.array(safe_post_comment_counts)).tolist()))
    
    unsafe_post_comments_abt_safety_per_comment_ratios = list(zip((np.array(unsafe_post_comments_abt_safety_count)).tolist(), 
                                                                (np.array(unsafe_post_comment_counts)).tolist()))
    
    post_stats[key].update({'comments_abt_safety_count': int(np.sum(safe_post_comments_abt_safety_count + unsafe_post_comments_abt_safety_count))})
    post_stats[key].update({'comments_abt_safety_mean': float(safe_mean(safe_post_comments_abt_safety_count + unsafe_post_comments_abt_safety_count))})

    post_stats[key].update({'safe_post_comments_abt_safety_count': int(np.sum(safe_post_comments_abt_safety_count))})
    post_stats[key].update({'safe_post_comments_abt_safety_mean': float(safe_mean(safe_post_comments_abt_safety_count))})

    post_stats[key].update({'unsafe_post_comments_abt_safety_count': int(np.sum(unsafe_post_comments_abt_safety_count))})
    post_stats[key].update({'unsafe_post_comments_abt_safety_mean': float(safe_mean(unsafe_post_comments_abt_safety_count))})

    post_stats[key].update({'safe_post_comments_abt_safety_per_comment_ratios': safe_post_comments_abt_safety_per_comment_ratios})
    post_stats[key].update({'unsafe_post_comments_abt_safety_per_comment_ratios': unsafe_post_comments_abt_safety_per_comment_ratios})

    post_stats[key].update({'safe_post_comments_abt_safety_per_comment_mean': safe_post_comments_abt_safety_per_comment_mean})
    post_stats[key].update({'unsafe_post_comments_abt_safety_per_comment_mean': unsafe_post_comments_abt_safety_per_comment_mean})


    with open(f"safe_posts_{key}.json", "w", encoding="utf-8") as f:
        json.dump(safe_posts, f, ensure_ascii=False, indent='\t')

    with open(f"unsafe_posts_{key}.json", "w", encoding="utf-8") as f:
        json.dump(unsafe_posts, f, ensure_ascii=False, indent='\t')

summation_fields = [key for key in post_stats['ig'].keys() if 'count' in key]
for field in summation_fields:
    post_stats['overall'].update({field: post_stats['ig'][field] + post_stats['fb'][field] + post_stats['tt'][field]})

with open(f"analysis.json", "w", encoding="utf-8") as f:
    json.dump(post_stats, f, ensure_ascii=False, indent='\t')
