#!/usr/bin/env python3
"""
Get Label
"""

from application.models.rule import LabelRule
from application.helpers.match import match


class GetLabel():# pylint: disable=too-few-public-methods
    """
    Filter Labels
    """

    def __init__(self):
        """
        Prepare Rules
        """
        self.rules = [x.to_mongo() for x in LabelRule.objects(enabled=True).order_by('sort_field')]

    @staticmethod
    def _check_label_match(condition, label, value):
        """
        Check if on of the given labels match the rule
        """
        if condition['match_on'] == 'label_name':
            match_on = label
        elif condition['match_on'] == 'label_value':
            match_on = value

        needed_value = condition['value']
        condition_match = condition['match']
        negate = condition['match_negate']
        label = label.lower()
        if match(match_on.lower(), needed_value.lower(), condition_match, negate):
            return True
        return False


    def filter_labels(self, labels):
        """
        Filter if labels match to a rule
        """
        matches = {}
        # pylint: disable=too-many-nested-blocks
        for label, value in labels.items():
            for rule in self.rules:
                hit = False
                for condition in rule['conditions']:
                    if self._check_label_match(condition, label, value):
                        hit = True
                        outcome = rule['outcome']
                        if not 'remove' in outcome and 'add' in outcome:
                            if 'strip' in outcome:
                                label = label.strip()
                                value = value.strip()
                            if 'lower' in outcome:
                                label = label.lower()
                                value = value.lower()
                            if 'replace' in outcome:
                                label = label.replace(' ', '_')
                                value = value.replace(' ', '_')
                            if 'replace_slash' in outcome:
                                label = label.replace('/', '-')
                                value = value.replace('/', '-')
                            if 'replace_special' in outcome:
                                for what in ['{', '}']:
                                    label = label.replace(what, '')
                                    value = value.replace(what, '')
                            matches[label] = value
                        break
                # Break out the rules if condition had a hit
                # we go on with next label then
                if hit:
                    break
        return matches
