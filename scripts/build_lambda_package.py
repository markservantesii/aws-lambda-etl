"""
Used for creating, updating and loading Lambda deployment packages
"""

import json
from pathlib import Path
import zipfile

import boto3


Path.ls = lambda d: list(d.iterdir())


class Env:
    lambda_dir = Path.cwd()/"lambda"
    lambda_package_dir = lambda_dir/"deployment-packages"

    lambda_func_name = "{lambda_name}"

    # bucket = 'ucop-fdw-dev-artifacts'
    key = 'lambda/{lambda_name}.zip'


def to_s3(bucket, key, filename):
    """ Upload file to S3.

       `bucket` is the name of the bucket to upload to.
       `key` is the full key of the file on s3. Example: path/to/file.txt
       `filename` is the path to the local file. Example /tmp/file.txt
    """
    s3 = boto3.client("s3")
    s3.upload_file(Filename=filename, Bucket=bucket, Key=key)


def remove_zipfile(zip_file):
    """ Removes a zipfile if it exists
    """
    path = Path(zip_file)
    if not path.exists():
        return

    try:
        path.unlink()
        print(f"{path.name} has been removed.")
    except:
        print(f"Cannot delete {path.name}")


def create_deployment_package(zip_path, lambda_path):
    """ Create a zip folder using python files from the lambda_path directory.
        Returns a dictionary containing the zip path (relative to the lambda dir)
        and the files added to the archive.
    """
    relative_path = zip_path.relative_to(Env.lambda_dir.parent)

    results = {
        'zipfile': '/'.join(relative_path.parts),
        'files': []
    }

    # add python files to the archive
    with zipfile.ZipFile(zip_path, 'w') as archive:
        python_files = Path(lambda_path).glob("*.py")
        python_files = [p for p in python_files if p.name != __file__]

        for p in python_files:
            fname = '/'.join(p.parts)
            archive.write(fname, p.name)
            results['files'].append(p.name)

    return results


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--lambda-name', help="Example: --lambda-name appflow-activator-lambda")
    parser.add_argument('--update', help="Boolean flag. Update the AWS Lambda Function", action="store_true")
    parser.add_argument('--upload', help="Boolean flag. Upload to s3", action="store_true")
    parser.add_argument('--bucket', help="Name of S3 bucket to upload deployment package")
    parser.add_argument('--rm', help="Remove deployment package after execution", action="store_true")

    args = parser.parse_args()

    # create lambda path and zip path
    lambda_path = Env.lambda_dir/args.lambda_name
    zip_path = Env.lambda_package_dir/f"{args.lambda_name}.zip"

    # delete old archive
    remove_zipfile(zip_path)

    # create a deployment package
    results = create_deployment_package(zip_path, lambda_path)

    # print results
    print(json.dumps(results, indent=4))


    bucket = args.bucket
    key = Env.key.format(lambda_name=args.lambda_name)
    func_name = Env.lambda_func_name.format(lambda_name=args.lambda_name)

    # Upload to S3
    if args.upload:
        
        filename = str(zip_path)
       
        try:
            to_s3(bucket=bucket, key=key, filename=filename)
            print(f"Successfully uploaded Lambda package to S3. Bucket: {bucket}, Key: {key}")

        except:
            print("Failed to upload zip file to S3")
            print(f"Bucket: {bucket}")
            print(f"Key: {key}")
            print(f"Zip file: {filename}")

    # Update Lambda function
    if args.update:
        try:

            client = boto3.client('lambda')

            response = client.update_function_code(
                FunctionName=func_name,
                S3Bucket=bucket,
                S3Key=key
            )
            print(f"Successfully updated Lambda Function: {func_name}")

        except:
            print("Unable to update Lambda Function.")



    # remove zipfile
    if args.rm:
        remove_zipfile(zip_path)

