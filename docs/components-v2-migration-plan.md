# Components V2 Migration Plan

## Executive Summary

This document outlines the comprehensive migration plan for migrating Astromorty from Discord's legacy component system (View-based) to Components V2 (LayoutView-based). This migration enables enhanced UI capabilities, better layout control, and access to modern Discord component features like Containers, Sections, and TextDisplay.

**Key Benefits:**
- Enhanced layout capabilities with Containers, Sections, and TextDisplay
- Up to 40 components per message (vs 25 in legacy)
- Better visual organization with Container accent colors
- Modern component system with improved flexibility
- Access to new component types (MediaGallery, File, Separator)

**Critical Constraints:**
- Cannot send `content`, `embeds`, `stickers`, or `polls` with Components V2
- Must use `TextDisplay` and `Container` instead of content/embeds
- Max 4000 characters across all TextDisplay items (accumulative)
- Max 40 components total (including nested)
- Once a message uses Components V2, it cannot be converted back

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Components V2 Overview](#components-v2-overview)
3. [Migration Strategy](#migration-strategy)
4. [Implementation Phases](#implementation-phases)
5. [Technical Implementation Details](#technical-implementation-details)
6. [Component-by-Component Migration Guide](#component-by-component-migration-guide)
7. [Testing Strategy](#testing-strategy)
8. [Rollback Plan](#rollback-plan)
9. [Timeline & Resources](#timeline--resources)

---

## Current State Analysis

### Current Component Usage

**Legacy View Classes (Require Migration):**

1. **`BaseConfirmationView`** (`src/astromorty/ui/views/confirmation.py`)
   - Uses `discord.ui.View`
   - Two buttons: Confirm and Cancel
   - Used by `ConfirmationDanger` and `ConfirmationNormal`
   - **Status:** Needs migration

2. **`BaseHelpView`** (`src/astromorty/help/components.py`)
   - Uses `discord.ui.View`
   - Complex navigation with select menus and buttons
   - Multiple subclasses: `HelpView`, `DirectHelpView`
   - Components: `CategorySelectMenu`, `CommandSelectMenu`, `SubcommandSelectMenu`, `BackButton`, `CloseButton`, `PaginationButton`
   - **Status:** Needs migration

3. **`TldrPaginatorView`** (`src/astromorty/ui/views/tldr.py`)
   - Uses `discord.ui.View`
   - Pagination buttons (Previous/Next)
   - Sends embeds with pagination
   - **Status:** Needs migration

4. **`XkcdButtons`** (`src/astromorty/ui/buttons.py`)
   - Uses `discord.ui.View`
   - Link buttons for xkcd comics
   - **Status:** Needs migration

5. **`GithubButton`** (`src/astromorty/ui/buttons.py`)
   - Uses `discord.ui.View`
   - Single link button
   - **Status:** Needs migration

6. **`_create_close_button_view`** (`src/astromorty/modules/utility/run.py`)
   - Creates dynamic View with close button
   - **Status:** Needs migration

**Already Using LayoutView:**

1. **`ConfigDashboard`** (`src/astromorty/ui/views/config/dashboard.py`)
   - Already uses `discord.ui.LayoutView`
   - Comprehensive example of Components V2 usage
   - **Status:** ✅ Already migrated (reference implementation)

**Modal Components:**

1. **`EditRankModal`** (`src/astromorty/ui/views/config/modals.py`)
   - Uses legacy `TextInput` with `label` parameter`
   - Should migrate to use `Label` component (recommended by Discord)
   - **Status:** Needs migration

2. **`CreateRankModal`** (`src/astromorty/ui/views/config/modals.py`)
   - Already uses `Label` component with `Select`
   - Uses legacy `TextInput` with `label` parameter
   - **Status:** Partial migration needed

### Current Message Sending Patterns

**Patterns Found:**
- `await ctx.send(embed=embed, view=view)` - Most common
- `await interaction.response.send_message(embed=embed, view=view)` - Slash commands
- `await interaction.message.edit(embed=embed, view=view)` - Updates
- `await source.send(embed=embed, view=view)` - Hybrid context

**Files Using Embeds + Views:**
- `src/astromorty/modules/tools/tldr.py` - TLDR pagination
- `src/astromorty/services/moderation/communication_service.py` - Moderation embeds
- Various command modules sending embeds with views

---

## Components V2 Overview

### Key Concepts

**LayoutView vs View:**
- **LayoutView** (V2): Modern system with enhanced capabilities
  - Define items as class variables (no manual `add_item` needed)
  - Buttons/Selects must be in ActionRow (except Section accessory)
  - Supports: ActionRow, Container, File, MediaGallery, Section, Separator, TextDisplay
  - Max 40 components total (including nested)
  
- **View** (Legacy): Still supported but limited
  - Max 25 top-level components
  - Max 5 ActionRows
  - Auto-arranges components

### Component Types & Limits

| Component | Type | Max Children | Char Limit | Usage |
|-----------|------|--------------|------------|-------|
| ActionRow | 1 | 5 buttons OR 1 select | - | Top-level in LayoutView |
| Button | 2 | - | 80 (label) | In ActionRow or Section accessory |
| StringSelect | 3 | 25 options | 150 (placeholder) | In ActionRow/Label |
| TextInput | 4 | - | 4000 (value), 100 (placeholder) | In Label only |
| Section | 9 | 1-3 TextDisplay | - | Top-level, 1 accessory |
| TextDisplay | 10 | - | 4000 (total per message) | LayoutView/Modal/Section/Container |
| Container | 17 | ≥1 | - | Top-level, embed-like box |
| Label | 18 | 1 component | 45 (text), 100 (description) | Modal only |

### Critical Constraints

1. **No Content/Embeds:** Cannot send `content`, `embeds`, `stickers`, or `polls` with Components V2
2. **TextDisplay Replacement:** Use `TextDisplay` for text content (supports markdown)
3. **Container Replacement:** Use `Container` for embed-like visual grouping
4. **Character Limits:** Max 4000 characters across all TextDisplay items (accumulative)
5. **Component Limits:** Max 40 components total (including nested)
6. **Irreversible:** Once a message uses Components V2, it cannot be converted back

### Embed to Container Migration

**Legacy Embed:**
```python
embed = discord.Embed(
    title="Title",
    description="Description",
    color=0x5865F2,
)
embed.add_field(name="Field", value="Value")
await ctx.send(embed=embed, view=view)
```

**Components V2 Equivalent:**
```python
class MyLayout(discord.ui.LayoutView):
    def __init__(self):
        super().__init__()
        container = discord.ui.Container(
            discord.ui.TextDisplay("# Title"),
            discord.ui.TextDisplay("Description"),
            discord.ui.Section(
                discord.ui.TextDisplay("**Field**\nValue"),
            ),
            accent_color=0x5865F2,
        )
        self.add_item(container)
        
        # ActionRow for buttons
        action_row = discord.ui.ActionRow()
        # ... add buttons to action_row
        self.add_item(action_row)

await ctx.send(view=MyLayout())
```

---

## Migration Strategy

### Approach: Phased Migration

**Phase 1: Foundation & Utilities**
- Create helper utilities for embed-to-container conversion
- Create TextDisplay formatters for common embed patterns
- Update documentation and rules

**Phase 2: Simple Components**
- Migrate simple button views (XkcdButtons, GithubButton)
- Migrate close button views
- Test with minimal complexity

**Phase 3: Medium Complexity**
- Migrate confirmation views
- Migrate TLDR paginator
- Handle pagination with Components V2

**Phase 4: Complex Components**
- Migrate help command system
- Handle complex navigation and state management
- Test edge cases

**Phase 5: Modals**
- Migrate modals to use Label components
- Update TextInput usage

**Phase 6: Integration & Testing**
- Update all command modules
- Comprehensive testing
- Performance validation

### Migration Principles

1. **Backward Compatibility:** Keep legacy Views working during migration
2. **Feature Parity:** Ensure all functionality works in V2
3. **Incremental:** Migrate one component at a time
4. **Testing:** Test each migration before proceeding
5. **Documentation:** Update docs as we migrate

---

## Implementation Phases

### Phase 1: Foundation & Utilities (Week 1)

**Tasks:**
1. Create embed-to-container conversion utilities
2. Create TextDisplay formatters
3. Update Cursor rules for Components V2
4. Create migration helper functions

**Deliverables:**
- `src/astromorty/ui/converters.py` - Embed/Container conversion utilities
- `src/astromorty/ui/formatters.py` - TextDisplay formatting helpers
- Updated `.cursor/rules/ui/cv2.mdc` with migration patterns
- Migration guide documentation

**Files to Create:**
```
src/astromorty/ui/
├── converters.py      # Embed → Container conversion
├── formatters.py      # TextDisplay formatting helpers
└── migration_helpers.py  # Common migration utilities
```

### Phase 2: Simple Components (Week 1-2)

**Tasks:**
1. Migrate `XkcdButtons` to LayoutView
2. Migrate `GithubButton` to LayoutView
3. Migrate `_create_close_button_view` helper
4. Update all usages

**Files to Modify:**
- `src/astromorty/ui/buttons.py`
- `src/astromorty/modules/utility/run.py`
- All files using these components

**Example Migration:**
```python
# Before
class XkcdButtons(discord.ui.View):
    def __init__(self, explain_url: str, webpage_url: str):
        super().__init__()
        self.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="Explainxkcd", url=explain_url))
        self.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="Webpage", url=webpage_url))

# After
class XkcdButtons(discord.ui.LayoutView):
    def __init__(self, explain_url: str, webpage_url: str):
        super().__init__()
        action_row = discord.ui.ActionRow()
        action_row.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="Explainxkcd", url=explain_url))
        action_row.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="Webpage", url=webpage_url))
        self.add_item(action_row)
```

### Phase 3: Medium Complexity (Week 2-3)

**Tasks:**
1. Migrate `BaseConfirmationView` and subclasses
2. Migrate `TldrPaginatorView`
3. Handle pagination with Components V2
4. Update embed-based messages to use Container

**Files to Modify:**
- `src/astromorty/ui/views/confirmation.py`
- `src/astromorty/ui/views/tldr.py`
- `src/astromorty/modules/tools/tldr.py`

**Key Challenges:**
- Converting embeds to Containers with TextDisplay
- Maintaining pagination state
- Handling message updates

**Example Migration:**
```python
# Before
class TldrPaginatorView(discord.ui.View):
    async def update_message(self, interaction: discord.Interaction):
        embed = EmbedCreator.create_embed(...)
        await interaction.response.edit_message(embed=embed, view=self)

# After
class TldrPaginatorView(discord.ui.LayoutView):
    def __init__(self, pages: list[str], title: str, user: discord.abc.User, bot: Astromorty):
        super().__init__(timeout=120)
        self.pages = pages
        self.page = 0
        self.title = title
        self.user = user
        self.bot = bot
        
        # Create container with TextDisplay
        self.container = discord.ui.Container()
        self._update_container()
        
        # Create action row with buttons
        self.action_row = discord.ui.ActionRow()
        self._update_buttons()
        
        self.add_item(self.container)
        self.add_item(self.action_row)
    
    def _update_container(self):
        self.container.clear_items()
        content = f"# {self.title} (Page {self.page + 1}/{len(self.pages)})\n\n{self.pages[self.page]}"
        self.container.add_item(discord.ui.TextDisplay(content))
    
    def _update_buttons(self):
        self.action_row.clear_items()
        # Add Previous/Next buttons
        # ...
    
    async def update_message(self, interaction: discord.Interaction):
        self._update_container()
        self._update_buttons()
        await interaction.response.edit_message(view=self)
```

### Phase 4: Complex Components (Week 3-4)

**Tasks:**
1. Migrate `BaseHelpView` and all subclasses
2. Migrate help command select menus
3. Migrate help command buttons
4. Handle complex navigation state
5. Update help command embed usage

**Files to Modify:**
- `src/astromorty/help/components.py`
- `src/astromorty/help/help_command.py` (if exists)
- All help command related files

**Key Challenges:**
- Complex state management
- Multiple select menus
- Navigation between views
- Embed conversion for help content

**Example Migration:**
```python
# Before
class BaseHelpView(discord.ui.View):
    def __init__(self, help_command: HelpCommandProtocol, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.help_command = help_command
        # Add select menus and buttons

# After
class BaseHelpView(discord.ui.LayoutView):
    def __init__(self, help_command: HelpCommandProtocol, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.help_command = help_command
        
        # Create container for content
        self.container = discord.ui.Container()
        self._build_content()
        
        # Create action rows for components
        self.select_row = discord.ui.ActionRow()
        self.button_row = discord.ui.ActionRow()
        self._build_components()
        
        self.add_item(self.container)
        self.add_item(self.select_row)
        self.add_item(self.button_row)
```

### Phase 5: Modals (Week 4)

**Tasks:**
1. Migrate `EditRankModal` to use Label components
2. Migrate `CreateRankModal` TextInput to use Label
3. Update all modal TextInput usage
4. Test modal interactions

**Files to Modify:**
- `src/astromorty/ui/views/config/modals.py`
- Any other files with modals

**Example Migration:**
```python
# Before
class EditRankModal(discord.ui.Modal):
    def __init__(self, ...):
        super().__init__(title="Edit Rank")
        self.rank_name = discord.ui.TextInput(
            label="Rank Name",  # Deprecated
            placeholder="...",
            required=True,
        )
        self.add_item(self.rank_name)

# After
class EditRankModal(discord.ui.Modal):
    def __init__(self, ...):
        super().__init__(title="Edit Rank")
        self.rank_name = discord.ui.Label(
            text="Rank Name",
            description="Enter the rank name",
            component=discord.ui.TextInput(
                custom_id="rank_name",
                placeholder="...",
                required=True,
            ),
        )
        self.add_item(self.rank_name)
    
    async def on_submit(self, interaction: discord.Interaction):
        name = self.rank_name.component.value  # Access via Label
```

### Phase 6: Integration & Testing (Week 5)

**Tasks:**
1. Update all command modules using embeds + views
2. Comprehensive testing of all migrated components
3. Performance testing
4. Edge case testing
5. Documentation updates
6. Code review

**Files to Review:**
- All command modules
- All UI components
- All interaction handlers

**Testing Checklist:**
- [ ] All buttons work correctly
- [ ] All select menus work correctly
- [ ] Pagination works correctly
- [ ] Navigation works correctly
- [ ] Modals work correctly
- [ ] Character limits respected
- [ ] Component limits respected
- [ ] Error handling works
- [ ] Timeout handling works
- [ ] Message updates work
- [ ] Ephemeral messages work

---

## Technical Implementation Details

### Embed to Container Conversion

**Helper Function:**
```python
# src/astromorty/ui/converters.py
def embed_to_container(embed: discord.Embed) -> discord.ui.Container:
    """Convert a Discord embed to a Components V2 Container.
    
    Parameters
    ----------
    embed : discord.Embed
        The embed to convert.
    
    Returns
    -------
    discord.ui.Container
        A Container with equivalent content.
    """
    items = []
    
    # Title
    if embed.title:
        items.append(discord.ui.TextDisplay(f"# {embed.title}"))
    
    # Description
    if embed.description:
        items.append(discord.ui.TextDisplay(embed.description))
    
    # Fields
    for field in embed.fields:
        field_text = f"**{field.name}**\n{field.value}"
        items.append(discord.ui.TextDisplay(field_text))
    
    # Footer
    if embed.footer:
        footer_text = embed.footer.text
        if embed.footer.icon_url:
            footer_text = f"{footer_text} [Icon]({embed.footer.icon_url})"
        items.append(discord.ui.TextDisplay(f"*{footer_text}*"))
    
    # Create container with accent color
    accent_color = embed.colour.value if embed.colour else None
    return discord.ui.Container(*items, accent_color=accent_color)
```

### TextDisplay Formatting Helpers

**Helper Functions:**
```python
# src/astromorty/ui/formatters.py
def format_embed_as_textdisplay(embed: discord.Embed) -> str:
    """Format an embed as TextDisplay markdown content."""
    parts = []
    
    if embed.title:
        parts.append(f"# {embed.title}")
    
    if embed.description:
        parts.append(embed.description)
    
    for field in embed.fields:
        parts.append(f"**{field.name}**\n{field.value}")
    
    if embed.footer:
        parts.append(f"*{embed.footer.text}*")
    
    return "\n\n".join(parts)

def truncate_textdisplay(content: str, max_length: int = 4000) -> str:
    """Truncate content to fit TextDisplay limits."""
    if len(content) <= max_length:
        return content
    return content[:max_length - 3] + "..."
```

### Message Sending Patterns

**Before (Legacy):**
```python
embed = discord.Embed(title="Title", description="Description")
view = MyView()
await ctx.send(embed=embed, view=view)
```

**After (Components V2):**
```python
class MyLayout(discord.ui.LayoutView):
    def __init__(self):
        super().__init__()
        container = embed_to_container(embed)
        self.add_item(container)
        # Add action rows with buttons

view = MyLayout()
await ctx.send(view=view)  # No embed parameter
```

### Pagination with Components V2

**Key Pattern:**
```python
class PaginatedLayout(discord.ui.LayoutView):
    def __init__(self, pages: list[str]):
        super().__init__()
        self.pages = pages
        self.current_page = 0
        
        # Container for content
        self.content_container = discord.ui.Container()
        self._update_content()
        
        # Action row for navigation
        self.nav_row = discord.ui.ActionRow()
        self._update_navigation()
        
        self.add_item(self.content_container)
        self.add_item(self.nav_row)
    
    def _update_content(self):
        self.content_container.clear_items()
        content = self.pages[self.current_page]
        self.content_container.add_item(discord.ui.TextDisplay(content))
    
    def _update_navigation(self):
        self.nav_row.clear_items()
        # Add Previous/Next buttons based on current_page
        # ...
    
    async def next_page(self, interaction: discord.Interaction):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self._update_content()
            self._update_navigation()
            await interaction.response.edit_message(view=self)
```

### Component ID Management

**Best Practice:**
```python
# Use constants for component IDs
TEXT_DISPLAY_ID = 100
CONFIRM_BUTTON_ID = 101
CANCEL_BUTTON_ID = 102

class MyLayout(discord.ui.LayoutView):
    text = discord.ui.TextDisplay("Content", id=TEXT_DISPLAY_ID)
    action_row = discord.ui.ActionRow()
    
    @action_row.button(label="Confirm", style=discord.ButtonStyle.primary, custom_id="confirm")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Update text display
        text = self.find_item(TEXT_DISPLAY_ID)
        text.content = "Updated content"
        await interaction.response.edit_message(view=self)
```

---

## Component-by-Component Migration Guide

### 1. BaseConfirmationView

**Current Implementation:**
- Uses `discord.ui.View`
- Two buttons: Confirm and Cancel
- Button styles updated dynamically

**Migration Steps:**
1. Change base class to `discord.ui.LayoutView`
2. Create `ActionRow` for buttons
3. Move buttons to ActionRow
4. Update button callbacks
5. Test confirmation flows

**Migrated Code:**
```python
class BaseConfirmationView(discord.ui.LayoutView):
    confirm_label: str
    confirm_style: discord.ButtonStyle

    def __init__(self, user: int) -> None:
        super().__init__()
        self.value: bool | None = None
        self.user = user
        
        # Create action row with buttons
        self.action_row = discord.ui.ActionRow()
        self._build_buttons()
        self.add_item(self.action_row)
    
    def _build_buttons(self):
        self.action_row.clear_items()
        
        # Confirm button
        confirm_btn = discord.ui.Button(
            label=self.confirm_label,
            style=self.confirm_style,
            custom_id="confirm",
        )
        confirm_btn.callback = self.confirm
        self.action_row.add_item(confirm_btn)
        
        # Cancel button
        cancel_btn = discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            custom_id="cancel",
        )
        cancel_btn.callback = self.cancel
        self.action_row.add_item(cancel_btn)
    
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ... existing logic
```

### 2. TldrPaginatorView

**Current Implementation:**
- Uses `discord.ui.View`
- Sends embeds with pagination
- Previous/Next buttons

**Migration Steps:**
1. Change to `discord.ui.LayoutView`
2. Convert embed to Container with TextDisplay
3. Create ActionRow for pagination buttons
4. Update message editing logic
5. Test pagination

**Key Changes:**
- Replace `EmbedCreator.create_embed()` with Container + TextDisplay
- Update `edit_message()` to only use `view` parameter
- Ensure character limits are respected

### 3. BaseHelpView

**Current Implementation:**
- Complex navigation system
- Multiple select menus
- Multiple buttons
- Embeds for content

**Migration Steps:**
1. Change to `discord.ui.LayoutView`
2. Convert embeds to Containers
3. Organize select menus in ActionRows
4. Organize buttons in ActionRows
5. Ensure component count stays under 40
6. Test all navigation flows

**Key Considerations:**
- Help content may exceed 4000 character limit
- May need pagination for long help content
- Multiple ActionRows for different component groups

### 4. XkcdButtons & GithubButton

**Current Implementation:**
- Simple link buttons
- No interaction callbacks

**Migration Steps:**
1. Change to `discord.ui.LayoutView`
2. Create ActionRow for buttons
3. Add buttons to ActionRow
4. Test link buttons work

**Note:** Link buttons don't send interactions, so migration is straightforward.

### 5. Modals

**Current Implementation:**
- Uses `TextInput` with `label` parameter (deprecated)
- Some already use `Label` component

**Migration Steps:**
1. Wrap all `TextInput` in `Label` components
2. Remove `label` parameter from `TextInput`
3. Access values via `label.component.value`
4. Test all modal submissions

---

## Testing Strategy

### Unit Tests

**Test Files to Create:**
- `tests/ui/test_converters.py` - Embed conversion tests
- `tests/ui/test_formatters.py` - TextDisplay formatting tests
- `tests/ui/test_layout_views.py` - LayoutView component tests

**Test Cases:**
1. Embed to Container conversion accuracy
2. TextDisplay formatting correctness
3. Component limit enforcement (40 components)
4. Character limit enforcement (4000 chars)
5. ActionRow weight system
6. Component ID management

### Integration Tests

**Test Scenarios:**
1. Confirmation views work correctly
2. Help command navigation works
3. TLDR pagination works
4. Button interactions work
5. Select menu interactions work
6. Modal submissions work
7. Message updates work
8. Timeout handling works

### Manual Testing Checklist

**For Each Migrated Component:**
- [ ] Component renders correctly
- [ ] All buttons work
- [ ] All select menus work
- [ ] Navigation works
- [ ] State management works
- [ ] Error handling works
- [ ] Timeout handling works
- [ ] Message updates work
- [ ] Character limits respected
- [ ] Component limits respected

### Performance Testing

**Metrics to Monitor:**
- Message send time
- Interaction response time
- Component rendering time
- Memory usage

---

## Rollback Plan

### If Migration Fails

**Immediate Rollback:**
1. Revert to previous commit
2. Restore legacy View implementations
3. Verify all functionality works

**Partial Rollback:**
- Keep successfully migrated components
- Revert problematic components to legacy
- Document issues for future migration

### Rollback Procedure

1. **Identify Issue:** Document the specific problem
2. **Assess Impact:** Determine scope of rollback needed
3. **Create Branch:** Create rollback branch from last known good state
4. **Revert Changes:** Revert specific files or commits
5. **Test:** Verify functionality restored
6. **Deploy:** Deploy rollback version
7. **Document:** Document issue and lessons learned

---

## Timeline & Resources

### Estimated Timeline

**Week 1: Foundation**
- Day 1-2: Create utilities and helpers
- Day 3-4: Update documentation
- Day 5: Review and testing

**Week 2: Simple Components**
- Day 1-2: Migrate XkcdButtons, GithubButton
- Day 3-4: Migrate close button views
- Day 5: Testing and fixes

**Week 3: Medium Complexity**
- Day 1-2: Migrate confirmation views
- Day 3-4: Migrate TLDR paginator
- Day 5: Testing and fixes

**Week 4: Complex Components**
- Day 1-3: Migrate help command system
- Day 4-5: Testing and fixes

**Week 5: Modals & Integration**
- Day 1-2: Migrate modals
- Day 3-4: Integration testing
- Day 5: Final review and documentation

**Total Estimated Time:** 5 weeks

### Resource Requirements

**Developer Time:**
- Primary developer: 5 weeks full-time
- Code review: 1 week part-time
- Testing: 1 week part-time

**Testing Resources:**
- Test Discord server
- Multiple test accounts
- Various permission levels

**Documentation:**
- Update component documentation
- Update migration guide
- Update examples

### Success Criteria

**Migration Complete When:**
1. All legacy View classes migrated to LayoutView
2. All embeds converted to Containers/TextDisplay
3. All tests passing
4. All manual testing complete
5. Documentation updated
6. Code review approved
7. No regressions in functionality
8. Performance acceptable

### Risk Mitigation

**Risks:**
1. **Character Limit Exceeded:** Implement truncation and pagination
2. **Component Limit Exceeded:** Optimize component usage, use Sections
3. **Breaking Changes:** Maintain backward compatibility during migration
4. **Performance Issues:** Monitor and optimize as needed
5. **User Experience:** Test thoroughly, gather feedback

**Mitigation Strategies:**
- Incremental migration (one component at a time)
- Comprehensive testing at each phase
- Rollback plan ready
- Documentation and examples
- Code review at each phase

---

## Additional Considerations

### Backward Compatibility

**Strategy:**
- Keep legacy Views working during migration
- Migrate incrementally
- Test both systems during transition
- Remove legacy code only after full migration

### Performance

**Optimizations:**
- Cache Container/TextDisplay creation
- Minimize component count
- Use Sections for efficient layouts
- Optimize TextDisplay content

### User Experience

**Improvements:**
- Better visual organization with Containers
- Enhanced layout flexibility
- More components per message (40 vs 25)
- Modern UI components

### Documentation Updates

**Files to Update:**
- `docs/content/developer/guides/components-v2.md` - Already exists, update with migration info
- `.cursor/rules/ui/cv2.mdc` - Update with migration patterns
- Component usage examples
- Migration guide (this document)

---

## Conclusion

This migration plan provides a comprehensive roadmap for migrating Astromorty to Discord Components V2. The phased approach ensures incremental progress with testing at each stage, minimizing risk and allowing for course correction as needed.

**Key Success Factors:**
1. Thorough testing at each phase
2. Incremental migration approach
3. Comprehensive documentation
4. Code review and quality assurance
5. User feedback and iteration

**Next Steps:**
1. Review and approve this plan
2. Set up development environment
3. Begin Phase 1 implementation
4. Establish testing procedures
5. Begin migration work

---

## References

- [Discord Components V2 Documentation](https://discord.com/developers/docs/interactions/message-components)
- [Discord.py LayoutView Documentation](https://discordpy.readthedocs.io/en/latest/api.html#layoutview)
- [Components V2 Guide (Internal)](docs/content/developer/guides/components-v2.md)
- [Cursor Rules: Components V2](.cursor/rules/ui/cv2.mdc)
- [Discord API Docs: Components Reference](external/discord-api-docs/docs/components/reference.mdx)

