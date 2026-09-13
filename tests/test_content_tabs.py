"""Tests for ContentTabs component."""


from thegent.docgen.content_tabs import ContentTabs


class TestContentTabs:
    """Tests for ContentTabs."""

    def test_init(self) -> None:
        """Test initialization."""
        ct = ContentTabs()
        assert ct.tabs == []

    def test_add_tab(self) -> None:
        """Test adding a tab."""
        ct = ContentTabs()
        ct.add_tab("Tab 1", "Content 1")
        assert len(ct.tabs) == 1
        assert ct.tabs[0]["label"] == "Tab 1"
        assert ct.tabs[0]["content"] == "Content 1"
        assert ct.tabs[0]["content_type"] == "text"
        assert ct.tabs[0]["default"] is False

    def test_add_multiple_tabs(self) -> None:
        """Test adding multiple tabs."""
        ct = ContentTabs()
        ct.add_tab("Tab 1", "Content 1", content_type="code", default=True)
        ct.add_tab("Tab 2", "Content 2", content_type="images", icon="pi pi-image")

        assert len(ct.tabs) == 2
        assert ct.tabs[0]["label"] == "Tab 1"
        assert ct.tabs[0]["content_type"] == "code"
        assert ct.tabs[0]["default"] is True

        assert ct.tabs[1]["label"] == "Tab 2"
        assert ct.tabs[1]["content_type"] == "images"
        assert ct.tabs[1]["icon"] == "pi pi-image"

    def test_render_empty(self) -> None:
        """Test rendering with no tabs."""
        ct = ContentTabs()
        assert ct.render() == ""

    def test_render_tabs(self) -> None:
        """Test rendering HTML."""
        ct = ContentTabs()
        ct.add_tab("Tab 1", "Content 1", default=True)
        ct.add_tab("Tab 2", "Content 2")

        html = ct.render()

        # Check for key elements
        assert '<div class="content-tabs vp-raw">' in html
        assert 'role="tablist"' in html
        assert "Tab 1" in html
        assert "Tab 2" in html
        assert "Content 1" in html
        assert "Content 2" in html

        # Check for active state
        assert 'class="tab-button active" role="tab" aria-selected="true" aria-controls="panel-0" id="tab-0"' in html
        assert 'class="tab-panel active" id="panel-0" role="tabpanel" aria-labelledby="tab-0"' in html

        # Check for inactive state
        assert 'class="tab-button " role="tab" aria-selected="false" aria-controls="panel-1" id="tab-1"' in html
        assert 'class="tab-panel " id="panel-1" role="tabpanel" aria-labelledby="tab-1" hidden="true"' in html

    def test_render_code_tab(self) -> None:
        """Test rendering code content type."""
        ct = ContentTabs()
        ct.add_tab("Code", "print('hello')", content_type="code")

        html = ct.render()
        assert "<pre><code>print('hello')</code></pre>" in html

    def test_render_image_tab(self) -> None:
        """Test rendering image content type."""
        ct = ContentTabs()
        ct.add_tab("Image", "https://example.com/image.png", content_type="images")

        html = ct.render()
        assert '<img src="https://example.com/image.png" alt="Image" />' in html

    def test_render_with_icon(self) -> None:
        """Test rendering tab with icon."""
        ct = ContentTabs()
        ct.add_tab("Icon Tab", "Content", icon="my-icon")

        html = ct.render()
        assert '<span class="tab-icon my-icon"></span> Icon Tab' in html
