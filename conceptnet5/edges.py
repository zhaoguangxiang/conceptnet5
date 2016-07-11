"""
Utilities for representing edges (assertions). Most notably, this module
includes the `make_edge` function, which builds the dictionary representing
an edge.
"""

from conceptnet5.uri import (assertion_uri, uri_prefix, conjunction_uri, is_concept)
import re


def make_edge(rel, start, end, dataset, license, sources,
              surfaceText=None, surfaceStart=None, surfaceEnd=None, weight=1.0):
    """
    Take in the information representing an edge (a justified assertion),
    and output that edge in dictionary form.

        >>> from pprint import pprint
        >>> from conceptnet5.uri import Licenses
        >>> e = make_edge(rel='/r/HasProperty',
        ...               start='/c/en/fire',
        ...               end='/c/en/hot',
        ...               dataset='/d/conceptnet/4/en',
        ...               license=Licenses.cc_attribution,
        ...               sources=[{'contributor': '/s/contributor/omcs/dev'}],
        ...               surfaceText='[[Fire]] is [[hot]]',
        ...               weight=1.0)
        >>> pprint(e)
        {'dataset': '/d/conceptnet/4/en',
         'end': '/c/en/hot',
         'features': ['/c/en/fire /r/HasProperty -',
                      '/c/en/fire - /c/en/hot',
                      '- /r/HasProperty /c/en/hot'],
         'license': 'cc:by/4.0',
         'rel': '/r/HasProperty',
         'sources': [{'contributor': '/s/contributor/omcs/dev'}],
         'start': '/c/en/fire',
         'surfaceEnd': 'hot',
         'surfaceStart': 'Fire',
         'surfaceText': '[[Fire]] is [[hot]]',
         'uri': '/a/[/r/HasProperty/,/c/en/fire/,/c/en/hot/]',
         'weight': 1.0}
    """
    pstart = uri_prefix(start)
    pend = uri_prefix(end)
    if is_concept(pstart) and is_concept(pend):
        features = [
            "%s %s -" % (pstart, rel),
            "%s - %s" % (pstart, pend),
            "- %s %s" % (rel, pend)
        ]
    else:
        features = []
    uri = assertion_uri(rel, start, end)

    assert isinstance(sources, list), sources
    assert all([isinstance(source, dict) for source in sources]), sources

    if surfaceStart is None or surfaceEnd is None:
        surfaceStart, surfaceEnd = extract_surface_terms(surfaceText)
    obj = {
        'uri': uri,
        'rel': rel,
        'start': start,
        'end': end,
        'dataset': dataset,
        'sources': sources,
        'features': features,
        'license': license,
        'weight': weight,
        'surfaceText': surfaceText,
        'surfaceStart': surfaceStart,
        'surfaceEnd': surfaceEnd
    }
    return obj


SURFACE_FORM_PATTERN = re.compile(r'\[\[(.*?)\]\]')


def extract_surface_terms(surface):
    """
    Some formats don't have separate slots for the surface text of the
    'start' and 'end' terms; we only record them as part of the overall
    surface text, in double brackets.

    A typical surface text will look like this:

        [[A dog]] has [[a tail]].

    Occasionally, there will be sentence frames that put the 'end' term
    before the 'start' term. These are marked with an asterisk.

        *[[A tail]] can belong to [[a dog]].

    This function returns the terms in their proper order -- 'surfaceStart'
    followed by 'surfaceEnd' -- so they can be indexed in the more flexible
    jsons and msgpack formats.
    """
    if not surface:
        return (None, None)
    surface_terms = SURFACE_FORM_PATTERN.findall(surface)
    if len(surface_terms) != 2:
        return (None, None)
    if surface.startswith('*'):
        surface_terms = surface_terms[::-1]
    return surface_terms


def uri_to_label(uri):
    return uri.split('/')[-1].replace('_', ' ')


def transform_for_linked_data(edge):
    """
    Modify an edge (assertion) in place to contain values that are appropriate
    for a Linked Data API.

    Although this code isn't actually responsible for what an API returns
    (see the conceptnet-web repository for that), it helps to deal with what
    edge dictionaries should contain here.

    The relevant changes are:

    - Remove the 'features' list
    - Make 'start', 'end', and 'rel' into dictionaries with an '@id' and
      'label', removing the separate 'surfaceStart' and 'surfaceEnd'
      attributes
    - All dictionaries should have an '@id'. For the edge itself, it's the
      URI. Without this, we get RDF blank nodes, which are awful.
    """
    if 'features' in edge:
        del edge['features']
    for source in edge['sources']:
        conj = conjunction_uri(*sorted(source.values()))
        source['@id'] = conj
    edge['@id'] = edge['uri']

    start_uri = edge['start']
    end_uri = edge['end']
    rel_uri = edge['rel']
    if edge['surfaceStart'] is not None:
        start_label = edge['surfaceStart']
    else:
        start_label = uri_to_label(edge['start'])
    if edge['surfaceEnd'] is not None:
        end_label = edge['surfaceEnd']
    else:
        end_label = uri_to_label(edge['end'])
    del edge['surfaceStart']
    del edge['surfaceEnd']
    rel_label = uri_to_label(edge['rel'])
    edge['start'] = {'@id': start_uri, 'label': start_label}
    edge['end'] = {'@id': end_uri, 'label': end_label}
    edge['rel'] = {'@id': rel_uri, 'label': rel_label}

    return edge
