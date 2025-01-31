""" 3scale specific widgets"""

import backoff
from widgetastic.exceptions import NoSuchElementException
from widgetastic.utils import ParametrizedLocator
from widgetastic.widget import GenericLocatorWidget, Widget
from widgetastic.widget import TextInput
from widgetastic_patternfly4 import ContextSelector, Navigation, PatternflyTable
from widgetastic_patternfly4 import Select
from widgetastic_patternfly4.navigation import check_nav_loaded

from testsuite.ui.exception import ItemNotPresentException


# Widget contains fill method which raise not implemented exception if widget is not fillable but pylint detect it as
# an abstract method
# pylint: disable=abstract-method
class RadioGroup(GenericLocatorWidget):
    """
    Radio group of 3scale pages. It contains both radio and check box elements, therefore it is not
    typical radio element. No control of option switching is implemented.

    In case of check box (like one on the bottom of the User Edit page), user needs to remember that
    possibility of multiple selected options is allowed (not an typical radio behaviour)
    """
    OPTIONS_SECTION = './fieldset/ol[contains(@class, "{}")]'

    OPTIONS = './li'
    OPTIONS_BY_ID = OPTIONS + '/label/input[@id="{}"]'

    def __init__(self, parent=None, locator=None, fieldset_id="", logger=None):
        super().__init__(parent, locator, logger)
        if fieldset_id:
            self.options_section = self.browser.element(self.OPTIONS_SECTION.format(fieldset_id))
        else:
            self.options_section = self.browser.element(locator)

    def select(self, options):
        """
        Select radio (check box) element from the list.
        :param options: String id-s of options
        """
        for option in options:
            element = self.browser.element(self.OPTIONS_BY_ID.format(option), parent=self.options_section)
            self._select_option(element)

    def clear_all(self):
        """
        Unset all option in radiogroup.
        """
        for element in self.browser.elements(self.OPTIONS, parent=self.options_section):
            self._select_option(element)

    @staticmethod
    def _select_option(element):
        # if 'is-unchecked' in element.get_attribute("class").split():
        element.click()


# pylint: disable=abstract-method
# Widget contains fill method which raise not implemented exception if widget is not fillable but pylint detect it as
# an abstract method
class CheckBoxGroup(RadioGroup):
    """CheckBox group of 3scale pages"""
    OPTIONS_BY_ID = './ol/li/label/input[@id="{}"]'


class ContextMenu(ContextSelector):
    """
    ContextMenu that extends ContextSelector lactated in Widgetastic PF4 libraries, but briefly adjusted
    to fit 3scale needs.
    """
    DEFAULT_LOCATOR = './/div[contains(@class, "pf-c-context-selector")]'
    BUTTON_LOCATOR = './/a[@title="Context Selector"]'


# pylint: disable=abstract-method
# Widget contains fill method which raise not implemented exception if widget is not fillable but pylint detect it as
# an abstract method
class NavigationMenu(Navigation):
    """
    Navigation menu for 3scale Views (menu on the left side of Audience, Product, Backend and Settings Views).
    widgetastic_patternfly4.Navigation was extended because it does not support item selection based on href
    which brought great code simplification for this component.

    As part of NavViews it handles steps to particular views. When `select_href` method is called with `href`
    argument (this argument is usually taken from destination View in a form of `path` variable),
    it finds right elements in Navigation, expands parent item if necessary and clicks correct item.
    """
    RELATED_RESOURCE = './/h2[@class="pf-c-nav__section-title"]'
    LOCATOR_START = './/nav[contains(@class, "pf-c-nav"){}]'
    # Product and backend navigation menu differs from others,
    # hence we need different ITEMS parameter than default one is.
    ITEMS = './section/ul/li/a| ./ul/li/a'
    # We need NAVIGATION_ITEMS due to navigation in subitems which cannot be done From ITEMS locator
    NAVIGATION_ITEMS = "./ul/li|./section/ul/li"
    SUB_ITEMS = './section/ul/li[contains(@class, "pf-c-nav__item")]'
    HREF_LOCATOR = SUB_ITEMS + '/a[contains(@href, "{}")]'

    @check_nav_loaded
    def currently_selected_item(self):
        """Returns the current navigation item."""
        return self.currently_selected[0]

    @check_nav_loaded
    def currently_selected_sub_item(self):
        """Returns the current navigation item."""
        return self.currently_selected[1]

    @check_nav_loaded
    def select_href(self, href):
        """
        Selects item from Navigation with specific href locator
        TODO: Add an exception like in Navigation select method
        """
        for element in self.browser.elements(self.NAVIGATION_ITEMS):
            element_href = element.find_element_by_tag_name("a").get_attribute("href")
            if element_href.endswith(href):
                self.browser.click(element)
                return
            item = self.browser.elements(self.HREF_LOCATOR.format(href), parent=element)
            if item:
                if "pf-m-expanded" not in element.get_attribute("class").split():
                    self.browser.click(element)
                    self.browser.wait_for_element(self.HREF_LOCATOR.format(href), parent=element, visible=True)
                self.browser.click(item[0])
                return

    def nav_resource(self):
        """
        Returns navigation title. This text is shown only in Product and Backend Views and it is used
        in `is_display` method to verify, if currently visible navigation menu (or whole View)
        is correctly loaded for particular Product or Backend.
        """
        return self.browser.element(self.RELATED_RESOURCE).text


# pylint: disable=abstract-method
# Widget contains fill method which raise not implemented exception if widget is not fillable but pylint detect it as
# an abstract method
class ThreescaleDropdown(GenericLocatorWidget):
    """Specific dropdown of 3scale pages"""

    def select_by_value(self, value):
        """Select given value from dropdown"""
        if value:
            self.browser.selenium.find_element_by_xpath(f"//select/option[@value='{value}']").click()


# pylint: disable=abstract-method
# Widget contains fill method which raise not implemented exception if widget is not fillable but pylint detect it as
# an abstract method
class AudienceTable(PatternflyTable):
    """
    Table defined by 3scale in Accounts view contains two headers: classic table header and header dedicated
    to search or row manipulation. This widget specifies correct header columns. It may extend already existing
    search implementation from PF4 in the future.
    """
    HEADERS = "./thead/tr[1]/th"


# pylint: disable=abstract-method
# Widget contains fill method which raise not implemented exception if widget is not fillable but pylint detect it as
# an abstract method
class ThreescaleCheckBox(GenericLocatorWidget):
    """Specific CheckBox button of 3scale pages"""

    def check(self, value=True):
        """Check or uncheck 3scale checkbox"""
        if value != self.is_checked():
            self.__element__().click()

    def is_checked(self):
        """
        :return if checkbox is checked
        """
        return self.__element__().get_attribute("checked") == "true"


# pylint: disable=abstract-method
# Widget contains fill method which raise not implemented exception if widget is not fillable but pylint detect it as
# an abstract method
class DeploymentRadio(RadioGroup):
    """Variation of 3scale radio group"""
    OPTIONS_SECTION = './/li[@id="{}"]/fieldset/ol'

    OPTIONS = './/li'
    OPTIONS_BY_ID = OPTIONS + '/label/input[@id="{}"]'


# pylint: disable=abstract-method
# Widget contains fill method which raise not implemented exception if widget is not fillable but pylint detect it as
# an abstract method
class PolicySection(Widget):
    """Widget representing Policies table section"""
    ROOT = ParametrizedLocator("//*[@id='policies']/div/section")
    POLICY_LIST = './ul/li'
    ITEMS_LOCATOR = './ul/li/article/h3'
    ITEM_LOCATOR = "./ul/li/article/h3[text()='{}']"
    ADD_POLICY_LOC = '.PolicyChain-addPolicy'
    CANCEL_LOC = '.PolicyChain-addPolicy--cancel'

    def __init__(self, parent=None, logger=None):
        Widget.__init__(self, parent, logger=logger)

    @property
    def items(self):
        """Returns a list of all policy registry items as strings."""
        return [self.browser.text(el) for el in self.browser.elements(self.ITEMS_LOCATOR, parent=self)]

    @property
    def is_policy_registry_displayed(self):
        """Returns opened state of the kebab."""
        return self.browser.is_displayed(self.ADD_POLICY_LOC)

    @property
    def first_policy(self):
        """
        Get First policy name in policy chain
        :return: Name of policy
        """
        return self.browser.elements('./ul/li[1]/article/h3')[0].text

    def add_policy(self, policy_name):
        """Opens Policy registry list and add policy by its name
        :param policy_name: name of the policy to be added
        """
        if not self.is_policy_registry_displayed:
            self.browser.click(self.CANCEL_LOC, parent=self)
        self.browser.click(self.ADD_POLICY_LOC, parent=self)
        self.item_select(policy_name)

    def edit_policy(self, policy_name):
        """
        :param policy_name:
        """
        if not self.is_policy_registry_displayed:
            self.browser.click(self.CANCEL_LOC, parent=self)
        if self.has_item(policy_name):
            self.item_select(policy_name)
        else:
            raise ItemNotPresentException('Item {!r} not found.'.format(policy_name))

    def drag_and_drop_policy(self, source, destination):
        """Drag and drop element from source element to destination
        :param
            source: string : name of source Policy
            destination: string : name of destination Policy
        """
        self.browser.drag_and_drop(source="./ul/li/article/h3[text()='{}']/ancestor::li/div/i".format(source),
                                   target="./ul/li/article/h3[text()='{}']/ancestor::li/div/i".format(destination))

    def has_item(self, item):
        """Returns whether the items exists.
        :param
            item: item name
        :return:
            Boolean - True if present, False if not.
        """
        return item in self.items

    # pylint: disable=raise-missing-from
    def item_element(self, item):
        """Returns a WebElement for given item name.
        :return WebElement
        """
        try:
            return self.browser.element(self.ITEM_LOCATOR.format(item), parent=self)
        except NoSuchElementException:
            raise ItemNotPresentException('Item {!r} not found.'.format(item))

    def item_select(self, item):
        """Opens the Policy registry and selects the desired policy.
        :param
            item: Item to be selected
        """
        self.logger.info('Selecting %r', item)
        if not self.has_item(item):
            raise ItemNotPresentException('Item "{item}" of policy is not present'.format(item=item))
        self.browser.click(self.item_element(item))


class ThreescaleSelect(Select):
    """Specific select for 3scale pages"""
    BUTTON_LOCATOR = "./div/button"


class DivBasedEditor(TextInput):
    """Widget of Div Based editor used to load Active doc specification"""

    def fill(self, value):
        """Fill value to Div Based Editor"""
        self.browser.click(self)
        self.browser.send_keys_to_focused_element(value)


# pylint: disable=abstract-method
# Widget contains fill method which raise not implemented exception if widget is not fillable but pylint detect it as
# an abstract method
class ActiveDocV2Section(Widget):
    """Active Doc V2 preview section"""
    ROOT = ParametrizedLocator('//*[@id="default_endpoint_list"]')
    ENDPOINTS_LIST = './li'
    ITEMS_LOCATOR = './li/ul/li/div/h3/span[2]/a'
    ITEMS_BUTTON_LOCATOR = './li/ul/li/div/h3/span[2]/a[text()="{}"]/ancestor::li/div[2]/form/div/input'
    RESPONSE_CODE_LOCATOR = './/*[contains(@class, "response_code")]/pre'

    def __init__(self, parent=None, logger=None):
        Widget.__init__(self, parent, logger=logger)

    @property
    def endpoints(self):
        """Returns a list of all endpoints registry items as strings."""
        return [self.browser.text(el) for el in self.browser.elements(self.ITEMS_LOCATOR, parent=self)]

    # pylint: disable=raise-missing-from
    def item_element(self, item):
        """Returns a WebElement for given item name.
        :return WebElement
        """
        try:
            return self.browser.element(self.ITEMS_BUTTON_LOCATOR.format(item), parent=self)
        except NoSuchElementException:
            raise NoSuchElementException('Item {!r} not found.'.format(item))

    @backoff.on_exception(backoff.fibo, NoSuchElementException, max_tries=4, jitter=None)
    def try_it_out(self, method):
        """Make test request
        :param method string eg. /post, /get
        """
        self.browser.click(self.item_element(method))

    @backoff.on_exception(backoff.fibo, NoSuchElementException, max_tries=4, jitter=None)
    def get_response_code(self):
        """Return response code called by method try_it_out"""
        return self.browser.text(self.RESPONSE_CODE_LOCATOR, parent=self)


class ThreescaleAnalyticsDropdown(GenericLocatorWidget):
    """Specific Dropdown menu of 3scale analytics pages"""

    def select(self, value):
        """Select specific metric to be displayed"""
        self.wait_displayed()
        self.click()
        self.browser.selenium.find_element_by_xpath(f"//*[text()='{value}']").click()

    def text(self):
        """Get text of metric"""
        self.wait_displayed()
        return self.browser.element(self.locator).text
