
"""

Lambda @ Edge Event Structure
    https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-event-structure.html

"""


def lambda_handler(event, context):
    request = event['Records'][0]['cf']['request']
    request['uri'] = '/'
    return request
    
