# This file is part of obs_base.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import unittest

import lsst.utils.tests
import lsst.afw.image
from lsst.obs.base import FilterDefinition, FilterDefinitionCollection
import lsst.pex.exceptions


class TestFilterDefinitionCollection(lsst.utils.tests.TestCase):
    def setUp(self):
        self.filters1 = FilterDefinitionCollection(FilterDefinition(physical_filter='abc', lambdaEff=123),
                                                   FilterDefinition(physical_filter='def',
                                                                    band='d',
                                                                    lambdaEff=456))
        self.filters2 = FilterDefinitionCollection(FilterDefinition(physical_filter='abc', lambdaEff=321),
                                                   FilterDefinition(physical_filter='def',
                                                                    band='dd',
                                                                    lambdaEff=654))
        FilterDefinitionCollection.reset()

    def test_singleton(self):
        self.filters1.defineFilters()
        self.assertEqual(lsst.afw.image.Filter('abc').getFilterProperty().getLambdaEff(), 123)
        self.assertEqual(lsst.afw.image.Filter('def').getFilterProperty().getLambdaEff(), 456)
        self.filters1.defineFilters()  # this should not change anything
        self.assertEqual(lsst.afw.image.Filter('abc').getFilterProperty().getLambdaEff(), 123)
        self.assertEqual(lsst.afw.image.Filter('def').getFilterProperty().getLambdaEff(), 456)
        with self.assertRaises(RuntimeError):
            self.filters2.defineFilters()
        # the defined filters should be unchanged
        self.assertEqual(lsst.afw.image.Filter('abc').getFilterProperty().getLambdaEff(), 123)
        self.assertEqual(lsst.afw.image.Filter('def').getFilterProperty().getLambdaEff(), 456)

    def test_reset(self):
        self.filters1.defineFilters()
        with self.assertRaises(RuntimeError):
            self.filters2.defineFilters()
        self.filters1.reset()
        # The new filters can be defiend and should replace the old ones.
        self.filters2.defineFilters()
        self.assertEqual(lsst.afw.image.Filter('abc').getFilterProperty().getLambdaEff(), 321)
        self.assertEqual(lsst.afw.image.Filter('def').getFilterProperty().getLambdaEff(), 654)

    def test_findAll(self):
        self.assertEqual(set(self.filters1.findAll('r')), set())
        matches = self.filters1.findAll('abc')
        self.assertEqual(len(matches), 1)
        match = list(matches)[0]
        self.assertEqual(match.physical_filter, 'abc')

    def test_physical_to_band(self):
        """Test that the physical_to_band dict returns expected values.
        """
        self.assertIsNone(self.filters1.physical_to_band['abc'])
        self.assertEqual(self.filters1.physical_to_band['def'], 'd')
        self.assertIsNone(self.filters2.physical_to_band['abc'])
        self.assertEqual(self.filters2.physical_to_band['def'], 'dd')


class TestFilterDefinition(lsst.utils.tests.TestCase):
    def setUp(self):
        lsst.afw.image.utils.resetFilters()
        self.filter_g = FilterDefinition(band="g",
                                         physical_filter="HSC-G",
                                         lambdaEff=1234,
                                         alias={'ABCDEFG'})
        self.filter_g2 = FilterDefinition(band="g",
                                          physical_filter="HSC-G2",
                                          afw_name='g2',
                                          lambdaEff=1235,
                                          alias={'HIJK'})

        self.physical_only = FilterDefinition(physical_filter="physical", lambdaEff=0)
        self.afw_name = FilterDefinition(physical_filter="afw_name",
                                         lambdaEff=5, afw_name="afw only")
        self.abstract = FilterDefinition(physical_filter="abstract", lambdaEff=42,
                                         band="abstract only")

    def testDefineFilters(self):
        """Test that a filter is properly defined in afw."""
        # the filter should not exist until we define it
        with self.assertRaises(lsst.pex.exceptions.NotFoundError):
            lsst.afw.image.Filter('g')
        with self.assertRaises(lsst.pex.exceptions.NotFoundError):
            lsst.afw.image.Filter('g2')
        with self.assertRaises(lsst.pex.exceptions.NotFoundError):
            lsst.afw.image.Filter('HSC-G')

        self.filter_g.defineFilter()
        filter = lsst.afw.image.Filter('g')
        filter_alias = lsst.afw.image.Filter('HSC-G')
        self.assertEqual(filter.getName(), 'g')
        # afw Filter stores the aliased name as the CannonicalName
        self.assertEqual(filter_alias.getCanonicalName(), 'g')
        self.assertEqual(filter, filter_alias)
        self.assertEqual(['ABCDEFG', 'HSC-G'], sorted(filter.getAliases()))

        self.filter_g2.defineFilter()
        filter2 = lsst.afw.image.Filter('g2')
        filter2_alias = lsst.afw.image.Filter('HSC-G2')
        self.assertEqual(filter2.getName(), 'g2')
        self.assertEqual(filter2_alias.getCanonicalName(), 'g2')
        self.assertEqual(filter2, filter2_alias)
        self.assertEqual(['HIJK', 'HSC-G2', 'g'], sorted(filter2.getAliases()))

    def test_physical_only(self):
        """physical_filter is the only name this filter has.
        """
        self.physical_only.defineFilter()
        filter = lsst.afw.image.Filter('physical')
        self.assertEqual(filter.getName(), 'physical')
        self.assertEqual([], sorted(filter.getAliases()))
        self.assertEqual(self.physical_only.makeFilterLabel(),
                         lsst.afw.image.FilterLabel(physical='physical'))

    def test_afw_name(self):
        """afw_name is the Filter name, physical_filter is an alias.
        """
        self.afw_name.defineFilter()
        filter = lsst.afw.image.Filter('afw only')
        filter_alias = lsst.afw.image.Filter('afw_name')
        self.assertEqual(filter.getName(), 'afw only')
        self.assertEqual(filter_alias.getCanonicalName(), 'afw only')
        self.assertEqual(['afw_name'], sorted(filter.getAliases()))
        self.assertEqual(self.afw_name.makeFilterLabel(),
                         lsst.afw.image.FilterLabel(physical='afw_name'))

    def test_abstract_only(self):
        """band is the Filter name, physical_filter is an alias.
        """
        self.abstract.defineFilter()
        filter = lsst.afw.image.Filter('abstract only')
        filter_alias = lsst.afw.image.Filter('abstract')
        self.assertEqual(filter.getName(), 'abstract only')
        self.assertEqual(filter_alias.getCanonicalName(), 'abstract only')
        self.assertEqual(['abstract'], sorted(filter.getAliases()))
        self.assertEqual(self.abstract.makeFilterLabel(),
                         lsst.afw.image.FilterLabel(band='abstract only', physical='abstract'))


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == '__main__':
    lsst.utils.tests.init()
    unittest.main()
