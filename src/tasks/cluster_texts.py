import math
from typing import Any, List
from uuid import uuid4
from copy import copy, deepcopy
import numpy as np
from collections import defaultdict
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from sklearn.cluster import AffinityPropagation
from dataclasses import dataclass, asdict, field
import random

from lib import s3 as s3_client
from lib.logger import logger
from lib.nlp import (
    get_pruned_stem,
    get_sentences,
)
from models.text import Text as TextModel
from models.clustering_helper import (
    load_first_embeddings_from_db,
)
from tasks.base_task import BaseTask
from tasks.base_task import record_start_finish_time_in_db



MAX_CLUSTER_SIZE = float("inf")
# To calculate radius for each bubble
MIN_RADIUS = 1
MIN_ALLOWED_DISTANCE = 1
MAX_NUM_TOKENS = 3

MAX_NUM_EXTRACTED_SUMMARY_SENTENCE = 5
MAX_NUM_KEYWORDS_FOR_TEXT = 1



@dataclass
class TextDraw:
    text: str
    x: float
    y: float
    dx: float = 0  # delta x from the center. The front end scaling for this would be different from x
    dy: float = 0
    font_size: float = 18


@dataclass
class KeywordItem:
    word: str
    count: int
    relevance_score: float
    kwd3uuid: str = None  # Kewyword uuid for D3 plot
    draw: TextDraw = None
    parent: TextDraw = None

    def __post_init__(self):
        self.relevance_score = round(self.relevance_score, 2)
    
    def set_relevance_score(self, score):
        self.relevance_score = round(score, 2)


@dataclass
class ClusterInfo:
    is_cluster_head: bool
    cluster_label: int


@dataclass
class XYCoord:
    x: float
    y: float


@dataclass
class ParentBubbleDrawItem:
    xy_coord: XYCoord
    radius: float
    bubble_uuid: str


@dataclass
class BubbleItem:
    embedding: List[float]  # high dimension embedding
    text: str = None
    uuid: str = None
    sequence_id: str = None
    tokens: list = field(default_factory=list)
    xy_coord: XYCoord = None
    cluster_info: ClusterInfo = None
    original_cluster_label: int = 0
    children: list = field(default_factory=list)  # list[BubbleItem]
    mid_dimension_coords: list = None
    children_count: int = None
    bubble_uuid: str = None  # d3 node unique id
    radius: float = None
    parent: ParentBubbleDrawItem = None
    keywords: list = None
    metadata: dict = None
    extracted_sentences_and_scores: list = field(default_factory=list)
    is_most_top_head: bool = False


def transform_json_data_to_structured(embedding_data):
    return [
        BubbleItem(
           text=item['text'],
           embedding=item['embedding'],
           uuid=item['uuid'],
           sequence_id=item['sequence_id'],
           tokens=item['tokens'],
        ) for item in embedding_data
    ]


def insert_reduced_2d_coords_tsne(data: List[BubbleItem]):
    """
    Runs the tSNE dimension reducsion algorithm
    and add the 2D dimension vectors to the original data
    """
    def get_high_dim_coords(e):
        # return copy(e.mid_dimension_coords)
        return copy(e.embedding)

    vect_list = []
    for e in data:
        vect_list.append(get_high_dim_coords(e))

    # reduce dimension
    vect_array = np.array(vect_list)
    low_dim_embeddings = TSNE(
        n_components=2,
        learning_rate=200,
        perplexity=30
    ).fit_transform(vect_array)

    # Merge back the low dimensions into the original data
    for i, item in enumerate(data):
        item.xy_coord = XYCoord(
            x=low_dim_embeddings[i][0],
            y=low_dim_embeddings[i][1],
        )


def insert_reduced_dimension_pca(data: List[BubbleItem], target_dim=50):
    """
    Lower the dimension to a mid range
    """
    def get_high_dim_coords(e):
        return copy(e.embedding)

    # get vectors
    vect_list = []
    for e in data:
        vect_list.append(get_high_dim_coords(e))
    vect_array = np.array(vect_list)
    # n_dim = min(target_dim, vect_array.shape[1])
    logger.debug(f"vect_list_pca={vect_list}")
    n_dim = target_dim

    pca = PCA(n_components=n_dim)
    low_dim = pca.fit_transform(vect_array)

    # Merge back the low dimensions into the original data
    for i, item in enumerate(data):
        item.mid_dimension_coords = list(low_dim[i])


def ap_cluster(x):
    """
    Clusters data using affinity propagation algorithm.
    """
    clustering = AffinityPropagation(
        random_state=0, damping=0.95
    ).fit(x)

    cluster_labels = clustering.labels_
    cluster_centers = clustering.cluster_centers_
    return cluster_labels, cluster_centers


def _get_clustered_data(data: List[BubbleItem]):
    """
    cluster a list of objects

    Returns
        Adds the clustering_info to each object in the input list of data
    """

    def get_coordinate(data_item: BubbleItem):
        """
        If one needs to cluster based on another set of
        coordinates, e.g., a reduced dimension, here
        should be modified. 
        """
        # TODO: Choose a dimention size
        # return copy(data_item.embedding)
        return [data_item.xy_coord.x, data_item.xy_coord.y]
        # return data_item.mid_dimension_coords


    # Cluster data
    coordinates = []
    for item in data:
        coordinates.append(get_coordinate(item))
    cluster_labels, cluster_centers = ap_cluster(np.array(coordinates))

    # add clustering info to the data structure
    for i, item in enumerate(data):
        item.cluster_info = ClusterInfo(
            is_cluster_head=get_coordinate(item) in cluster_centers,
            cluster_label=cluster_labels[i]
        )

    # sort data
    return sorted(
        data,
        key=lambda x: (x.cluster_info.cluster_label, not x.cluster_info.is_cluster_head)
    )


def _transform_flat_clusters_to_tree(clustered_data: List[BubbleItem]):
    """
    transform a list of object into a nested list based on clustering info.
    If there is only one cluster, it retruns the same input

    Arg:
        clustered_data (list): A flat list of objects

    Return:
        (list): a hierarchical list of objects
    """
    # check the number of cluster heads; return if there is only one cluster
    num_cluster_heads = 0
    for item in clustered_data:
        if item.cluster_info.is_cluster_head:
            num_cluster_heads += 1
    if num_cluster_heads == 1:
        return clustered_data

    # Break down if there are more than one cluster
    items_by_cluster_label = defaultdict(list)
    result = []

    for d in clustered_data:
        items_by_cluster_label[d.cluster_info.cluster_label].append(d)

    for _, val in items_by_cluster_label.items():
        if len(val) > 1:
            head = BubbleItem(
                embedding=[],
                original_cluster_label=val[0].cluster_info.cluster_label,
                children=val
            )
        else:
            head = val[0]
        result.append(head)
    return result


def cluster_based_on_keywords(data: List[BubbleItem]):
    """
    cluster text with the same keyword together
    """
    bubbles_by_token = defaultdict(list)
    for d in data:
        if d.tokens:
            keyword = get_pruned_stem(d.tokens[0]['token'])
        else:
            keyword = None
            logger.warning(f"No keywords for text item={d.text}")
        bubbles_by_token[keyword].append(d)
    new_data = []
    for _, value in bubbles_by_token.items():
        if len(value) > 1:
            x_coords = np.array( [node.xy_coord.x for node in value] )
            y_coords = np.array( [node.xy_coord.y for node in value] )
            x = np.mean(x_coords)
            y = np.mean(y_coords)

            head = BubbleItem(
                embedding=[],
                children=value,
                xy_coord=XYCoord(x=x, y=y)
            )
        else:
            head = value[0]
        new_data.append(head)
    return new_data


def cluster_and_transform_to_tree(
    data: List[BubbleItem],  # flat list
    include_original_cluster_label=False
):
    """
    Gets an array of input data with dimension and performs
    clustering on them and represents data as hierarchical

    This function can be called recursively
    """
    data = deepcopy(data)

    clustered_data = _get_clustered_data(data)

    if include_original_cluster_label:
        for item in clustered_data:
            item.original_cluster_label = item.cluster_info.cluster_label

    nested_clusters = _transform_flat_clusters_to_tree(clustered_data)
    return nested_clusters


def put_tree_under_head(data: List[BubbleItem]):
    head = BubbleItem(embedding=[], is_most_top_head=True)
    head.children = data
    return head


def trim_tree_breadth(head: BubbleItem, max_cluster_size=MAX_CLUSTER_SIZE):
    """
    BFS traverse the nested clustering and break down if a node has too many
    children
    """
    frontiers = [head]
    while frontiers:
        next = frontiers.pop(0)
        if len(next.children) > max_cluster_size:
            next.children = cluster_and_transform_to_tree(next.children)
        frontiers.extend(next.children)
    
    return head


def insert_children_count(head: BubbleItem):
    """
    Add total number of children for each node recursively
    """
    if not head.children:
        head.children_count = 0
        return 0
    sum = 0
    for node in head.children:
        sum += 1 
        if node.children_count is not None:
            sum += node.children_count
        else:
            sum += insert_children_count(node)
    head.children_count = sum
    return sum


def insert_bubble_uuid(head: BubbleItem):
    """
    Traverse the tree of data and insert a unique identifier for
    each node that will be used for d3 distinctions later
    """
    if not head:
        return
    frontiers = [head]
    while frontiers:
        next = frontiers.pop(0)
        next.bubble_uuid = str(uuid4())
        frontiers.extend(next.children)


leaf_coords_memo = defaultdict(list)
def _get_leaf_coords(head: BubbleItem):
    global leaf_coords_memo
    if head.bubble_uuid in leaf_coords_memo:
        return leaf_coords_memo[head.bubble_uuid]

    if not head:
        return []
    if len(head.children) == 0:
        return [head.xy_coord]
    coords = []
    for child in head.children:
        coords.extend(_get_leaf_coords(child))

    if head.bubble_uuid:
        leaf_coords_memo[head.bubble_uuid] = coords

    return coords


def insert_cluster_heads_coords(head: BubbleItem):
    if not head:
        return
    frontiers = [head]
    while frontiers:
        next = frontiers.pop(0)
        frontiers.extend(next.children)

        if len(next.children) > 0:
            x_coords = np.array( [c.x for c in _get_leaf_coords(next)] )
            y_coords = np.array( [c.y for c in _get_leaf_coords(next)] )
            x = np.mean(x_coords)
            y = np.mean(y_coords)
            next.xy_coord = XYCoord(x=x, y=y)


def _get_radius_multiplier(clustering_data):
    """
    get the max multiplier that is used to inflate the bubble sizes
    Args
        clustering_data : list(dict) : a list of objects. Objects have a key
                            for number of children
    """
    multiplier = float("inf")
    if len(clustering_data) < 2:
        multiplier = 0
    for i in range(len(clustering_data)):
        for j in range(i + 1, len(clustering_data)):
            filled = max(
                np.sqrt(clustering_data[i].children_count),
                np.sqrt(clustering_data[j].children_count)
            )
            p1 = np.array([
                float(clustering_data[i].xy_coord.x),
                float(clustering_data[i].xy_coord.y)
            ])
            p2 = np.array([
                float(clustering_data[j].xy_coord.x),
                float(clustering_data[j].xy_coord.y)
            ])
            d = np.linalg.norm(p1 - p2)
            if d > MIN_ALLOWED_DISTANCE:
                multiplier = min(multiplier, d / filled)
    return multiplier


def insert_radius(head: BubbleItem):
    """
    Insert the radius in all object in the tree, and also for
    each object, insert the radius of their parent
    """
    radius_multiplier_factor = _get_radius_multiplier(head.children)

    frontiers = copy(head.children)
    while frontiers:
        next = frontiers.pop(0)
        frontiers.extend(next.children)

        if next.children:
            next.radius = max([
                np.sqrt(next.children_count) * radius_multiplier_factor,
                MIN_RADIUS
            ])
        else:
            next.radius = MIN_RADIUS


def insert_parents_info(head: BubbleItem):
    """
    Insert parents coordinates and radius in each child
    """
    if not head:
        return
    frontiers = [head]
    while frontiers:
        current = frontiers.pop(0)
        frontiers.extend(current.children)

        if current.is_most_top_head:
            for child in current.children:
                child.parent = ParentBubbleDrawItem(
                    xy_coord=copy(child.xy_coord),
                    radius=0,
                    bubble_uuid=child.bubble_uuid,
                )
        else:
            for child in current.children:
                child.parent = ParentBubbleDrawItem(
                    xy_coord=copy(current.xy_coord),
                    radius=current.radius,
                    bubble_uuid=current.bubble_uuid,
                )



def _group_keywords_by_count(keywords: List[KeywordItem]):
    """
    Remove punctuations and stem the words and then insert
    the counts of the stemmed root words.
    
    This function is unit tested; to see the input output
    examples, refer to the tests.
    """
    token_count = defaultdict(int)
    token_relevance_score = defaultdict(float)
    for kw in keywords:
        token_count[kw.word] += kw.count
        token_relevance_score[kw.word] += kw.relevance_score
    # Construct a new list of results
    res = []
    seen = set()
    for kw in keywords:
        if kw.word not in seen:
            kw.count = token_count[kw.word]
            kw.set_relevance_score(token_relevance_score[kw.word])
            # Need to assigns a new d3 uuid since this is a new entity 
            kw.kwd3uuid = str(uuid4())
            res.append(kw)
            seen.add(kw.word)
    # sort by counts and then relevance scores
    res.sort(key=lambda x: (-x.count, -x.relevance_score))
    return res


def _group_stemmed_keywords_by_counts(keywords: List[KeywordItem]):
    keywords = deepcopy(keywords)
    for item in keywords:
        item.draw.text = item.word
        item.word = get_pruned_stem(item.word)
    return _group_keywords_by_count(keywords)


def insert_and_return_keywords(head: BubbleItem):
    """
    Performs a post order tree traverse to insert all the keywords. 
    """
    keywords = []
    children = head.children
    if children:
        for child in children:
            keywords.extend(insert_and_return_keywords(child))
        keywords = _group_stemmed_keywords_by_counts(keywords)
    else:
        if head.tokens and len(head.tokens) > 0:
            keywords = [
                KeywordItem(
                    word=get_pruned_stem(token['token']),
                    count=1,
                    relevance_score=token['similarity'],
                    kwd3uuid = str(uuid4()),
                    draw=TextDraw(
                        x=float(head.xy_coord.x),
                        y=float(head.xy_coord.y),
                        text=token['token'],
                    ),
                )
                for token in head.tokens[:MAX_NUM_KEYWORDS_FOR_TEXT]
            ]
    head.keywords = deepcopy(keywords)
    return head.keywords


def insert_wordcloud_draw_properties(head: BubbleItem):
    """
    Inser the draw properties such as x and y coordinates
    for the word cloud
    """
    frontiers = [head]
    while frontiers:
        current = frontiers.pop(0)
        frontiers.extend(current.children)

        if len(current.children) > 1 and current.radius:
            center_x = float(current.xy_coord.x)
            center_y = float(current.xy_coord.y)
            radius = round( current.radius )
            if len(current.keywords) == 1:
                kw = current.keywords[0]
                kw.draw.x = center_x
                kw.draw.y = center_y
                kw.draw.font_size = round(10 * math.log(kw.count * round(10 * kw.relevance_score)), 1)
            else:
                for kw in current.keywords:
                    kw.draw.x = center_x
                    kw.draw.dx = radius * random.gauss(0, 0.2) 
                    kw.draw.y = center_y
                    kw.draw.dy = radius * random.gauss(0, 0.35)
                    kw.draw.font_size = round(10 * math.log(kw.count * round(10 * kw.relevance_score)), 1)


def _insert_keywords_parents_info_for_a_first_layer_node(current: BubbleItem):
    for child in current.children:
        for kw in child.keywords:
            kw.parent = copy(kw)
            kw.parent.dx = 0
            kw.parent.dy = 0
            kw.parent.parent = None


def _insert_keywords_parents_info_for_a_second_layer_or_deeper_node(current: BubbleItem):
    for child in current.children:
        for kw in child.keywords:
            kw.parent = None
            # find the keyword in the parent's set of keyword
            for parent_kw in current.keywords:
                if kw.word == parent_kw.word:
                    kw.parent = parent_kw
                    break


def insert_keywords_parents_info(head: BubbleItem):
    if not head:
        return
    frontiers = [head]
    while frontiers:
        current = frontiers.pop(0)
        frontiers.extend(current.children)

        if current.is_most_top_head:
            _insert_keywords_parents_info_for_a_first_layer_node(current)
        else:
            _insert_keywords_parents_info_for_a_second_layer_or_deeper_node(current)


def insert_meta_data(head: BubbleItem):
    """
    Insert the metadat field that includes the following
        metadata:
            max_x, min_x
            max_y, min_y
    """
    min_x = float("inf")
    max_x = float("-inf")
    min_y = float("inf")
    max_y = float("-inf")
    frontiers = deepcopy(head.children)
    while frontiers:
        next = frontiers.pop(0)
        min_x = min(next.xy_coord.x - next.radius, min_x)
        min_y = min(next.xy_coord.y - next.radius, min_y)
        max_x = max(next.xy_coord.x + next.radius, max_x)
        max_y = max(next.xy_coord.y + next.radius, max_y)
        frontiers.extend(next.children)

    head.metadata = {
        'x': {
            'max': max_x,
            'min': min_x,
        },
        'y': {
            'max': max_y,
            'min': min_y,
        },
        'radius': {
            'max': max(max_x - min_x, max_y - min_y)
        }
    }


def remove_text_for_cluster_heads(head: BubbleItem):
    frontiers = [head]
    while frontiers:
        current = frontiers.pop(0)
        frontiers.extend(current.children)
        #
        if current.children:
            current.text = None


def insert_stuff(head: BubbleItem):
    """
    Insert stuff
    """
    insert_children_count(head)
    insert_bubble_uuid(head)
    insert_cluster_heads_coords(head)
    insert_radius(head)
    insert_parents_info(head)
    insert_meta_data(head)
    insert_and_return_keywords(head)
    insert_wordcloud_draw_properties(head)
    insert_keywords_parents_info(head)
    remove_text_for_cluster_heads(head)


def extract_summary_sentences(head: BubbleItem):
    """
    Extranct summary sentences and insert them in the head
    """
    @dataclass
    class SentenceClustering:
        sentence: str
        cluster_label: int
        is_cluster_head: bool
        score: float = 0

    @dataclass
    class SentenceScoreItem:
        sentence: str
        score: float

    #
    # Get all texts under the node
    #
    texts = []
    frontiers = [head]
    while frontiers:
        current = frontiers.pop(0)
        frontiers.extend(current.children)
        if current.text:
            texts.append(current.text)
    #
    # split to sentences 
    #
    sentences = []
    for t in texts:
        sentences.extend(get_sentences(t))
    sentences = list(set(sentences))
    #
    # load embedding for sentences
    #
    sent_embeddings = []
    for sent in sentences:
        embedding = TextModel().get_embedding_by_text(sent)  # had to use TextModel() instead of TextModel so that I can mock it in test
        if embedding:
            sent_embeddings.append({
                'sent': sent,
                'embedding': list(embedding),
            })
        else:
            logger.warning(f"Could not find sentence embedding for sentence={sent}")

    #
    # Cluster sentences to find cluster heads
    #
    cluster_labels, cluster_centers = ap_cluster(np.array(
        [e['embedding'] for e in sent_embeddings]
    ))

    #
    # Form the data structure and sort them
    #
    sent_clusterings = []
    for i, item in enumerate(sent_embeddings):
        sent_clusterings.append(SentenceClustering(
            sentence= item['sent'],
            cluster_label=cluster_labels[i],
            is_cluster_head=item['embedding'] in cluster_centers,
        ))
    sent_clusterings.sort(key=lambda x: (x.cluster_label, not x.is_cluster_head))

    #
    # Assign relevance scores based on the cluster size for each cluster head 
    #
    total_size = 0
    cluster_size = defaultdict(int)
    for item in sent_clusterings:
        cluster_size[item.cluster_label] += 1
        total_size += 1
    for item in sent_clusterings:
        item.score = cluster_size.get(item.cluster_label, 0) / total_size
    
    #
    # Expunge items that are not cluster heads
    #
    sent_scores = [
        SentenceScoreItem(
            sentence=item.sentence,
            score=item.score,
        ) for item in sent_clusterings if item.is_cluster_head
    ]
    sent_scores.sort(key=lambda x: -x.score)

    #
    # Insert back into the data structure
    #
    head.extracted_sentences_and_scores = sent_scores[:MAX_NUM_EXTRACTED_SUMMARY_SENTENCE]


def traverse_and_extract_summary_sentences(nodes: List[BubbleItem]):
    frontiers = copy(nodes)
    while frontiers:
        current = frontiers.pop(0)
        frontiers.extend(current.children)
        if current.children:
            extract_summary_sentences(current)


def get_formatted_item(item: BubbleItem):
    """
    Arg:
        An input item
    """
    entry = {
        'x': float(item.xy_coord.x),
        'y': float(item.xy_coord.y),
        'uuid': item.uuid,
        'd3uuid': item.bubble_uuid,
        'text': item.text,
        'cluster_label': int(item.original_cluster_label),
        'children_count': item.children_count,
        'radius': float(item.radius),
        'parent': {
            'x': float(item.parent.xy_coord.x),
            'y': float(item.parent.xy_coord.y),
            'radius': float(item.parent.radius),
            'd3uuid': item.parent.bubble_uuid,
        } if item.parent else None,
        'children': [],
        'keywords': [asdict(kw) for kw in item.keywords],
        'summary_sentences': [asdict(e) for e in item.extracted_sentences_and_scores]
    }
    return entry


def get_reshaped_data(head: BubbleItem):
    """
    """
    if not head:
        return
    new_node = {}
    if not head.is_most_top_head:
        new_node = get_formatted_item(head)
    new_node['children'] = [
        get_reshaped_data(c) for c in head.children
    ]
    return new_node


def _load_embeddings_from_db(sequence_ids):
    embedding_data = []
    for i in sequence_ids:
        embedding_data.extend(load_first_embeddings_from_db(i))
    return embedding_data


def _expunge_tree(head):
    frontiers = [head]
    while frontiers:
        next = frontiers.pop(0)
        frontiers.extend(copy(next.children))
        # 
        next.embedding = []
        # next.text = ''
        next.tokens = []
        next.mid_dimension_coords = []


class ClusterTexts(BaseTask):

    public_description = "Classifying and summarizing texts to create the Babel Map"

    def validate_raw_data(self, raw_data):
        MIN_NUM_INPUTS = 2
        if len(raw_data) < MIN_NUM_INPUTS:
            logger.debug(f"Less than {MIN_NUM_INPUTS} input texts for job_id={self.job_id}")
            self.append_event(
                event_lookup_key='not_enough_input_samples',
                job_id=self.job_id,
            )
            raise ValueError(f"There should be at least {MIN_NUM_INPUTS} inputs.")

    @record_start_finish_time_in_db
    def execute(self):
        """
        Loads all the texts and embeddings for a sequence id,
        performs dimension reduction and clustering, and saves
        the results to database

        Args:
            sequence_ids (list[str]): A list of ids for all
                the texts in the sequence that will be processed
        """
        TOTAL_NUMBER_OF_STEPS = 11
        current_progress = 0
        self.record_progress(current_progress, TOTAL_NUMBER_OF_STEPS)

        sequence_id = self.kwargs['sequence_id']

        logger.debug("Loading data from DB...")
        raw_data = _load_embeddings_from_db([sequence_id])
        current_progress += 1
        self.record_progress(current_progress, TOTAL_NUMBER_OF_STEPS)

        try:
            self.validate_raw_data(raw_data)
        except ValueError as e:
            self.record_progress(TOTAL_NUMBER_OF_STEPS, TOTAL_NUMBER_OF_STEPS)
            raise


        logger.debug("Formatting raw_data...")
        data = transform_json_data_to_structured(raw_data)
        current_progress += 1
        self.record_progress(current_progress, TOTAL_NUMBER_OF_STEPS)


        # # dimention reduction -- pca
        # logger.debug("Reducing dimension to a mid range dimension...")
        # insert_reduced_dimension_pca(data)
        # current_progress += 1
        # self.record_progress(current_progress, TOTAL_NUMBER_OF_STEPS)

        # dimention reduction and inserting 2D coords -- tSNE
        logger.debug("Reducing dimension to 2D...")
        insert_reduced_2d_coords_tsne(data)
        current_progress += 1
        self.record_progress(current_progress, TOTAL_NUMBER_OF_STEPS)

        # clustering based on common keywords
        # data = cluster_based_on_keywords(data)
        # current_progress += 1
        # self.record_progress(current_progress, TOTAL_NUMBER_OF_STEPS)


        # clustering affinity Propagation
        logger.debug("First round of clustering data...")
        clusters = cluster_and_transform_to_tree(data, include_original_cluster_label=True)
        current_progress += 1
        self.record_progress(current_progress, TOTAL_NUMBER_OF_STEPS)

        # Put a head on top
        head = put_tree_under_head(clusters)
        current_progress += 1
        self.record_progress(current_progress, TOTAL_NUMBER_OF_STEPS)

        # Trim down
        logger.debug("Trim tree and breakdown big clusters")
        head = trim_tree_breadth(head)
        current_progress += 1
        self.record_progress(current_progress, TOTAL_NUMBER_OF_STEPS)

        # Insert stuff
        logger.debug("Insert data")
        insert_stuff(head)
        current_progress += 1
        self.record_progress(current_progress, TOTAL_NUMBER_OF_STEPS)

        # insert representative sentences 
        logger.debug("Extract summary sentences for cluster heads")
        traverse_and_extract_summary_sentences(head.children)
        current_progress += 1
        self.record_progress(current_progress, TOTAL_NUMBER_OF_STEPS)

        # _expunge(data)
        # _expunge_tree(head)
        # breakpoint()

        logger.debug("Get reshaped data...")
        data_dict = get_reshaped_data(head)
        current_progress += 1
        self.record_progress(current_progress, TOTAL_NUMBER_OF_STEPS)

        data_dict['metadata'] = head.metadata

        #
        # with open("_temp.txt", "w") as f:
        #     f.write(json.dumps(data_dict, indent=4))
        #

        logger.debug(f"🌩️ Uploading data to S3 sequence_id={sequence_id} ...")
        s3_client.upload_clustering_data_to_s3(sequence_id, data_dict)
        current_progress += 1
        self.record_progress(current_progress, TOTAL_NUMBER_OF_STEPS)

        # To make the progress to 100%
        self.record_progress(current_progress, current_progress)

        logger.debug("Done!")
