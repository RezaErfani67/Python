#get from parchildest collection to parent
# db.getCollection("address").aggregate(
#     {
#         "$lookup": {
# 			"localField": 'user',
# 			"from": 'user',
# 			"foreignField": '_id',
# 			"pipeline": [
# 				{
# 					"$lookup": {
# 						"localField": 'group',
# 						"from": 'group',
# 						"foreignField": '_id',
# 						as: 'groups',
# 					},
# 				},
# 			],
# 			as: 'users',
# 	    	}
# 		})

#get from parent to childest
# db.getCollection("group").aggregate(
#     {
#         "$lookup": {
# 			"localField": '_id',
# 			"from": 'user',
# 			"foreignField": 'group',
# 			"pipeline": [
# 				{
# 					"$lookup": {
# 						"localField": '_id',
# 						"from": 'address',
# 						"foreignField": 'user',
# 						as: 'address',
# 					},
# 				},
# 			],
# 			as: 'users',
# 	    	}
# 		})

def convert_to_lookup(relationship_map):
    lookup_array = []
    for key, value in relationship_map.items():
        lookup = {
            '$lookup': {
                'from': value['from'],
                'localField': value['localField'],
                'foreignField': value['foreignField'],
                'as': key
            }
        }
        if 'nested' in value:
            nested_lookup = convert_to_lookup(value['nested'])
            lookup['$lookup']['pipeline'] = nested_lookup
        lookup_array.append(lookup)
    return lookup_array

# Test data
relationship_map = {
    'user': {
        'from': 'user',
        'localField': '_id',
        'foreignField': 'group',
        'nested': {
            'addresses': {
                'from': 'address',
                'localField': '_id',
                'foreignField': 'user'
            }
        }
    },
    'test': {
        'from': 'user',
        'localField': 'test',
        'foreignField': 'test'
    }
}

# Convert to lookup
result = convert_to_lookup(relationship_map)
print(result)
