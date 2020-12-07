CLUSTERED_DATA = [
    {
        'uuid': 1,
        'cluster_info': {
            'is_cluster_head': True,
            'cluster_label': 0
        }
    },
    {
        'uuid': 2,
        'cluster_info': {
            'is_cluster_head': False,
            'cluster_label': 0
        }
    },
    {
        'uuid': 3,
        'cluster_info': {
            'is_cluster_head': True,
            'cluster_label': 1
        }
    },
    {
        'uuid': 4,
        'cluster_info': {
            'is_cluster_head': True,
            'cluster_label': 2
        }
    },
    {
        'uuid': 5,
        'cluster_info': {
            'is_cluster_head': False,
            'cluster_label': 2
        }
    },
    {
        'uuid': 6,
        'cluster_info': {
            'is_cluster_head': False,
            'cluster_label': 2
        }
    },
    {
        'uuid': 7,
        'cluster_info': {
            'is_cluster_head': False,
            'cluster_label': 2
        }
    }
]

NESTED_DATA = [
    {
        'uuid': 1,
        'cluster_info': {
            'is_cluster_head': True,
            'cluster_label': 0
        },
        'children': [
            {
                'uuid': 1,
                'cluster_info': {
                    'is_cluster_head': True,
                    'cluster_label': 0
                },
                'children': []
            },
            {
                'uuid': 2,
                'cluster_info': {
                    'is_cluster_head': False,
                    'cluster_label': 0
                },
                'children': []
            }
        ]
    },
    {
        'uuid': 3,
        'cluster_info': {
            'is_cluster_head': True,
            'cluster_label': 1
        },
        'children': []
    },
    {
        'uuid': 4,
        'cluster_info': {
            'is_cluster_head': True,
            'cluster_label': 2
        },
        'children': [
            {
                'uuid': 4,
                'cluster_info': {
                    'is_cluster_head': True,
                    'cluster_label': 2
                },
                'children': []
            },
            {
                'uuid': 5,
                'cluster_info': {
                    'is_cluster_head': False,
                    'cluster_label': 2
                },
                'children': []
            },
            {
                'uuid': 6,
                'cluster_info': {
                    'is_cluster_head': False,
                    'cluster_label': 2
                },
                'children': []
            },
            {
                'uuid': 7,
                'cluster_info': {
                    'is_cluster_head': False,
                    'cluster_label': 2
                },
                'children': []
            }
        ]
    },
]

MULTI_NESTED_DATA = {
    'children': [
        {
            'uuid': 1,
            'cluster_info': {
                'is_cluster_head': True,
                'cluster_label': 0
            },
            'children': [
                {
                    'uuid': 1,
                    'cluster_info': {
                        'is_cluster_head': True,
                        'cluster_label': 0
                    },
                    'children': []
                },
                {
                    'uuid': 2,
                    'cluster_info': {
                        'is_cluster_head': False,
                        'cluster_label': 0
                    },
                    'children': []
                }
            ]
        },
        {
            'uuid': 3,
            'cluster_info': {
                'is_cluster_head': True,
                'cluster_label': 1
            },
            'children': []
        },
        {
            'uuid': 4,
            'cluster_info': {
                'is_cluster_head': True,
                'cluster_label': 2
            },
            'children': [
                {
                    'uuid': 4,
                    'cluster_info': {
                        'is_cluster_head': True,
                        'cluster_label': 2
                    },
                    'children': []
                },
                {
                    'uuid': 5,
                    'cluster_info': {
                        'is_cluster_head': False,
                        'cluster_label': 2
                    },
                    'children': [
                        {
                            'uuid': 6,
                            'cluster_info': {
                                'is_cluster_head': False,
                                'cluster_label': 2
                            },
                            'children': []
                        },
                        {
                            'uuid': 7,
                            'cluster_info': {
                                'is_cluster_head': False,
                                'cluster_label': 2
                            },
                            'children': []
                        }
                    ]
                }
            ]
        },
    ]
}


MULTI_NESTED_DATA_W_CHILDREN_COUNT = {
    'children_count': 9,
    'children': [
        {
            'uuid': 1,
            'cluster_info': {
                'is_cluster_head': True,
                'cluster_label': 0
            },
            'children_count': 2,
            'children': [
                {
                    'uuid': 1,
                    'cluster_info': {
                        'is_cluster_head': True,
                        'cluster_label': 0
                    },
                    'children_count': 0,
                    'children': []
                },
                {
                    'uuid': 2,
                    'cluster_info': {
                        'is_cluster_head': False,
                        'cluster_label': 0
                    },
                    'children_count': 0,
                    'children': []
                }
            ]
        },
        {
            'uuid': 3,
            'cluster_info': {
                'is_cluster_head': True,
                'cluster_label': 1
            },
            'children_count': 0,
            'children': []
        },
        {
            'uuid': 4,
            'cluster_info': {
                'is_cluster_head': True,
                'cluster_label': 2
            },
            'children_count': 4,
            'children': [
                {
                    'uuid': 4,
                    'cluster_info': {
                        'is_cluster_head': True,
                        'cluster_label': 2
                    },
                    'children_count': 0,
                    'children': []
                },
                {
                    'uuid': 5,
                    'cluster_info': {
                        'is_cluster_head': False,
                        'cluster_label': 2
                    },
                    'children_count': 2,
                    'children': [
                        {
                            'uuid': 6,
                            'cluster_info': {
                                'is_cluster_head': False,
                                'cluster_label': 2
                            },
                            'children_count': 0,
                            'children': []
                        },
                        {
                            'uuid': 7,
                            'cluster_info': {
                                'is_cluster_head': False,
                                'cluster_label': 2
                            },
                            'children_count': 0,
                            'children': []
                        }
                    ]
                }
            ]
        },
    ]
}
