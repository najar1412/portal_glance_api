# TODO: classes needed?
import datetime
from .models import assignment, tag_table, Collection, Tag, Asset, Base, Footage, User, Item, Image


# dev functions
def __reset_db(session, engine):
    """DEV: drops tables and rebuild"""
    session.close()

    try:
        import sqlalchemy
        meta = sqlalchemy.MetaData(engine)
        meta.reflect()
        meta.drop_all()
    except:
        print('----------------------------')
        print('Table have not been deleted.')
        print('----------------------------')
    try:
        Base.metadata.create_all(engine)
    except:
        print('---------------------------')
        print('Tables have not been built.')
        print('---------------------------')

    print('----------------------------------------')
    print('Tables removed, and re-built successful.')
    print('----------------------------------------')

    # TODO: is return True 'pythonic', something better?
    return True

# helper functions
def make_dict(item_list):
    """ takes list of database objects, returns dict repr of objects. """
    # TODO: using '__tablename__' on objects does the same jobs as 'item_type'
    # any point in having it as column?
    result = []

    # for each database object, build dict, 'item', from data.
    for item_object in item_list:
        item = {}
        for column in item_object.__table__.columns:
            item[column.name] = str(getattr(item_object, column.name))

        # additional many-to-many data
        # init tags
        # TODO: '.append(str(tag.name))' could more info be used here? like
        # {'name': 'int(assets rate?)'} maybe too advanced?
        if item_object.item_type == 'asset':
            # If object is asset
            # init tags
            item['tags'] = []
            assets_tags = item_object.tags

            for tag in assets_tags:
                item['tags'].append(str(tag.name))

            # init collections
            item['collections'] = []
            # get assets collections via many-to-many
            assets_collections = item_object.collections

            # append collection objects to 'item'
            for collection in assets_collections:
                item['collections'].append(
                    (int(collection.id), str(collection.name))
                )

        elif item_object.item_type == 'collection':
            # If object is a collection
            # init tags
            item['tags'] = []
            collections_tags = item_object.tags

            for tag in collections_tags:
                item['tags'].append(str(tag.name))

            # init assets
            item['assets'] = []
            assignments = item_object.assets

            for assignment in assignments:
                bla = make_dict((assignment,))[0]
                item['assets'].append(
                    bla
                )

        elif item_object.item_type == 'footage':
            # If object is asset
            # init tags
            try:
                # TODO: IMP tags for footage
                item['tags'] = []
                assets_tags = item_object.tags

                for tag in assets_tags:
                    item['tags'].append(str(tag.name))
            except:
                pass

            try:
                # TODO: IMP collections for footage
                # init collections
                item['collections'] = []
                # get assets collections via many-to-many
                footage_collections = item_object.collections

                # append collection objects to 'item'
                for collection in footage_collections:
                    item['collections'].append(
                        (int(collection.id), str(collection.name))
                    )
            except:
                pass

        result.append(item)

    # return database objects as dicts.
    return result


def to_dict(item_list):
    """ takes list of database objects, returns dict repr of objects. """
    # TODO: using '__tablename__' on objects does the same jobs as 'item_type'
    # any point in having it as column?
    result = []

    # for each database object, build dict, 'item', from data.
    for item_object in item_list:
        item = {}
        for column in item_object.__table__.columns:
            item[column.name] = str(getattr(item_object, column.name))

        result.append(item)

    # return database objects as dicts.
    return result



# user functions
def post_collection(session, **kwarg):
    """Posts collection to the database
    Return: collection; 'newly posted collection'
    """

    payload = {}
    data = {}

    # build POST data payload query from user data, **kwarg
    # TODO: issues between the name 'tag' coming from the frontend, and 'tags'
    # in the backend. Make consistant.
    for k, v in kwarg.items():
        if k == 'tags':
            bla = v.split(' ')
            payload['tags'] = bla
        elif k == 'assets':
            bla = v.split(' ')
            payload['assets'] = [int(i) for i in bla]
        else:
            payload[k] = v
    del payload['tag']

    # validate payload agaisnt database columnns, automate None to empty fields
    for column in Collection.__table__.columns:
        if column.name in payload:
            data[column.name] = payload[column.name]
        elif column.name not in payload:
            data[column.name] = None
        else:
            pass

    # init collection object
    collection = Collection(
        name=data['name'], image=data['image'], author=data['author']
    )

    # append default cover to Collection object, if 'None'
    # TODO: can possibly do this during validation?
    if data['image_thumb'] == None:
        collection.image_thumb = 'default_cover.jpg'
    else:
        collection.image_thumb = data['image_thumb']

    # commit new collection.
    session.add(collection)

    if 'tags' in payload:
        for tag in payload['tags']:
            newtag = Tag(name=str(tag))
            session.add(newtag)
            collection.tags.append(newtag)

    if 'assets' in payload:
        for asset in payload['assets']:
            collection.assets.append(asset)

    session.commit()

    return collection


def post_asset(session, **kwarg):
    """Posts asset to the database
    Return: asset; 'new posted aset'
    """

    payload = {}
    data = {}

    # process user input
    for k, v in kwarg.items():
        if k == 'tag':
            bla = v.split(' ')
            payload[k] = bla
        else:
            payload[k] = v

    # remove attri that arnt in the database
    for column in Asset.__table__.columns:
        if column.name in payload:
            data[column.name] = payload[column.name]
        elif column.name not in payload:
            data[column.name] = None
        else:
            pass

    # Database entry
    asset = Asset(
        name=data['name'], image=data['image'],
        image_thumb=data['image_thumb'], attached=data['attached'],
        author=data['author']
    )

    # I think i put this here because the asset had to be 'init' with
    # session.add() because i needed to append new tags?
    # TODO: understand before better, refactor, multiple session hits might not
    # be needed?
    session.add(asset)

    if 'tag' in payload:
        for tag in payload['tag']:
            newtag = Tag(name=str(tag))
            session.add(newtag)
            asset.tags.append(newtag)

    # commit changes to database
    session.commit()

    return asset


def get_collections(session):
    """Returns list of dict collection objects"""
    # querys for all Collection objects in order of id, appends to list
    # TODO: This should return objects in order of moddate
    collections = []
    for collection in session.query(Collection).order_by(Collection.id):
        collections.append(collection)

    # return raw db objects
    return collections


def get_assets(session):
    """Returns all asset objects"""
    # querys for all asset objects in order of moddate, appends to list
    assets = []
    for asset in session.query(Asset).order_by(Asset.moddate):
        assets.append(asset)

    # returns raw db objects
    return assets


def get_footages(session):
    """Returns all footage objects"""
    # querys for all asset objects in order of moddate, appends to list
    footages = []
    for footage in session.query(Footage).order_by(Footage.moddate):
        assets.append(footage)

    # returns raw db objects
    return footages


def get_asset_by_id(session, id):
    """Return asset object as a dict using Asset.id"""
    # querys for asset object
    asset_by_id = session.query(Asset).get(id)

    # returns raw asset
    return asset_by_id


def get_collection_by_id(session, id):
    """Returns collection object as dict using Collection.id"""
    # querys for collection object
    collection_by_id = session.query(Collection).get(id)

    return collection_by_id


# TODO: Can all these get_query_* re refactored to a single methods? using
# flags or something.
def get_query(session, userquery):
    """takes list of words and returns related objects"""
    # TODO: currently searching every table with every query term, multiple
    # searches. gotta be a better way. look into postgres joins?
    result = {}

    # makes users query a dict
    for k, v in userquery.items():
        query = {k: str(v).split()}

    # querying through many-to-many relationships leaves us with an
    # instrumentedlist which needs to be exracted before using make_dict
    item_list = []
    for term in query['query']:
        # return list of tags
        taglists = session.query(Tag).filter_by(name=term).all()
        # for each tag
        for tag in taglists:
            # if one exists
            if tag.item:
                # get asset assigned to tag and append to list, 'item_list'
                for item in tag.item:
                    item_list.append(item)
            # get collection assigned to tag and append to list, 'item_list'
            elif tag.collection_tags:
                for item in tag.collection_tags:
                    item_list.append(item)

    return item_list


def get_query_flag(session, flag):
    """ Returns list of flagged items """
    result = []
    # collection assets
    assets = session.query(Asset).filter(int(flag)>0).all()
    for x in assets:
        result.append(make_dict((x,))[0])

    # collect collections
    collections = session.query(Collection).filter(int(flag)>0).all()
    for x in collections:
        result.append(make_dict((x,))[0])

    return result


def patch_asset(session, **user_columns):
    """updates asset fields using user data"""
    # TODO: This is a pretty heftly function... needs refactoring

    # init query dict
    query = {}
    # asset id
    id = int(user_columns['id'])

    # build list of assets column names for validation
    asset_columns = Asset.__table__.columns.keys()

    # validate user data and build query dict, from data.
    for k, v in user_columns.items():
        if k in asset_columns:
            query[k] = v

        else:
            pass

        # additional many-to-many data
        if k == 'collections':
            query[k] = v.split()

        elif k == 'tags':
            query['tags'] = v.split()

        else:
            pass

    # once all user data is validated and ready to append, get asset object.
    asset = session.query(Asset).get(id)

    # Process user data and update asset object fields.
    # TODO: is there a better way to handle these sort of 'flags'?
    for k, v in query.items():
        if k == 'name':
            asset.name = v

        elif k == 'image':
            asset.image = v

        elif k == 'image_thumb':
            asset.image_thumb = v

        elif k == 'attached':
            asset.attached = v

        elif k == 'tags':
            # process asset tags
            for tag in v:
                # create new Tag object and append to asset object
                # TODO: Could this be a point to implement a 'set{}' for
                # duplicutes
                newtag = Tag(name=str(tag))
                session.add(newtag)

                asset.tags.append(newtag)

        elif k == 'flag':
            # process flag field
            # if 'flag' is true value is increased
            if int(query['flag']) == 1:
                # TODO: is a try/except needed here?
                try:
                    asset.flag += 1

                except TypeError:
                    asset.flag = 0
                    asset.flag += 1

            # if 'flag' is false value is reduced
            elif int(query['flag']) == 0:
                asset.flag -= 1

            # is the 'else:' 'pythonic'?
            else:
                pass

        elif k == 'collections':
            for collection_id in query['collections']:
                # get Collection object using collection.id
                existingcollection = session.query(Collection).get(collection_id)
                # append existing collection to assets collections
                asset.collections.append(existingcollection)

        else:
            pass

    # Finish asset object
    # append object moddate
    asset.moddate = datetime.datetime.utcnow()

    session.add(asset)
    session.commit()

    result = make_dict((asset,))

    # Returns asset object
    return result


def patch_collection(session, id, **user_columns):
    """updates users defined columns with user defined values"""
    # TODO: This is a pretty heftly function... needs refactoring
    # init query dict

    #init query dict
    query = {}

    # build list of collections columnnams for validation
    collection_columns = Collection.__table__.columns.keys()

    # validdate uer data and build query dict, from data.
    for k, v in user_columns.items():
        if k in collection_columns:
            query[k] = v

        else:
            pass

        # additional many-to-many data
        if k == 'assets':
            query[k] = v.split()

        elif k == 'tags':
            query[k] = v.split()

        elif k == 'remove_assets':
            query[k] = v.split()

        else:
            pass

    # once all user data is alidate and ready to append, get collection object
    collection = session.query(Collection).get(id)

    # process user data and update collection object fields.
    # TODO: is there a better way to handle these sort of 'flags'?
    for k, v in query.items():
        if k == 'name':
            collection.name = v

        elif k == 'image':
            collection.image = v

        elif k == 'image_thumb':
            collection.image_thumb = v

        elif k == 'assets':
            for asset_id in v:
                # TODO: dont use try/except for control flow
                try:
                    # get asset object and append to collection
                    newasset = session.query(Asset).get(int(asset_id))
                    collection.assets.append(newasset)

                except:
                    pass

        elif k == 'remove_assets':
            for asset_id in v:
                # TODO: dont use try/except for this
                try:
                    # get asset object and remove from collection.
                    # TODO: is there a quicker way? without getting the object first?
                    removeasset = session.query(Asset).get(int(asset_id))
                    collection.assets.remove(removeasset)

                except:
                    pass

        elif k == 'tags':
            for x in v:
                # create to Tag objects and append to collection.
                # TODO: Could this be a point to implement a 'set{}' for
                # duplicutes
                newtag = Tag(name=str(x))
                session.add(newtag)

                collection.tags.append(newtag)

        elif k == 'flag':
            # process flag field
            # if 'flag' is true value is increased
            if int(query['flag']) == 1:
                # TODO: is a try/except needed here?
                try:
                    collection.flag += 1

                except TypeError:
                    collection.flag = 0
                    collection.flag += 1

            # if 'flag' is false value is reduced
            elif int(query['flag']) == 0:
                collection.flag -= 1

            # is the 'else:' 'pythonic'?
            else:
                pass
        else:
            pass

    # Finish asset object
    # append object moddate
    collection.moddate = datetime.datetime.utcnow()

    session.add(collection)
    session.commit()

    result = make_dict((collection,))

    # Returns collection object
    return result


def del_asset(session, asset_id):
    """deletes asset object"""
    # TODO: also delete physical files.
    # TODO: IMP aset database?
    # get collection
    asset = session.query(Asset).filter(Asset.id=='{}'.format(asset_id)).first()
    # delete collection
    session.delete(asset)
    # and commit to session.
    session.commit()

    return True


def del_collection(session, collection_id):
    """deletes collection object"""
    # TODO: also delete physical files.
    # TODO: IMP aset database?
    # get collection
    collection = session.query(Collection).filter(Collection.id=='{}'.format(collection_id)).first()
    # delete collection
    session.delete(collection)
    # and commit to session.
    session.commit()

    return True


def post_user(session, **kwarg):
    data = {}

    # process user input
    for k, v in kwarg.items():
        data[k] = v

    # Database entry
    user = User(
        username=data['username'], password=data['password']
    )

    session.add(user)
    session.commit()

    return user


def get_user(session, **kwarg):

    # TODO: if test == NONETYPE, return False

    test = session.query(User).filter_by(username=kwarg['username']).first()

    if test is not None and test.password == kwarg['password']:
        result = True
    else:
        result = False

    # returns raw db objects
    return result


def new_image(session):
    item = Image(
        name = 'test image name',
        item_loc = 'test image',
        item_thumb = 'test image thumb',
        author = 'test author'
    )

    session.add(item)
    session.commit()


def new_footage(session):
    item = Footage(
        name = 'test footage name',
        item_loc = 'test item_loc',
        item_thumb = 'test item_thumb',
        author = 'test author'
    )

    session.add(item)
    session.commit()


def new_geometry(session):
    item = Geometry(
        name = 'test footage name',
        item_loc = 'test item_loc',
        item_thumb = 'test item_thumb',
        author = 'test author'
    )

    session.add(item)
    session.commit()
