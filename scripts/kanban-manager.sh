#!/bin/bash

# Kanban Board Manager - Sync issues with project board
# Creates visual workflow for multi-agent system

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NUMBER=3
OWNER="IgorGanapolsky"
REPO="SuperPassword"

echo -e "${BLUE}📊 Kanban Board Manager${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}\n"

# Function to get project ID
get_project_id() {
    gh api graphql -f query='
    query($owner: String!, $number: Int!) {
      user(login: $owner) {
        projectV2(number: $number) {
          id
          title
        }
      }
    }' -f owner="$OWNER" -F number="$PROJECT_NUMBER" --jq '.data.user.projectV2.id'
}

# Function to get field IDs
get_field_ids() {
    local project_id=$1
    gh api graphql -f query='
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 20) {
            nodes {
              ... on ProjectV2Field {
                id
                name
              }
              ... on ProjectV2SingleSelectField {
                id
                name
                options {
                  id
                  name
                }
              }
            }
          }
        }
      }
    }' -f projectId="$project_id" --jq '.data.node.fields.nodes'
}

# Function to add issue to project
add_issue_to_project() {
    local project_id=$1
    local issue_id=$2
    
    gh api graphql -f query='
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item {
          id
        }
      }
    }' -f projectId="$project_id" -f contentId="$issue_id" --jq '.data.addProjectV2ItemById.item.id'
}

# Function to update issue status
update_issue_status() {
    local project_id=$1
    local item_id=$2
    local field_id=$3
    local option_id=$4
    
    gh api graphql -f query='
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $projectId,
        itemId: $itemId,
        fieldId: $fieldId,
        value: {
          singleSelectOptionId: $optionId
        }
      }) {
        projectV2Item {
          id
        }
      }
    }' -f projectId="$project_id" -f itemId="$item_id" -f fieldId="$field_id" -f optionId="$option_id"
}

# Main execution
echo -e "${YELLOW}🔍 Finding project...${NC}"
PROJECT_ID=$(get_project_id)

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Project not found! Creating new project...${NC}"
    
    # Create new project
    PROJECT_ID=$(gh api graphql -f query='
    mutation($ownerId: ID!, $title: String!) {
      createProjectV2(input: {
        ownerId: $ownerId,
        title: $title
      }) {
        projectV2 {
          id
        }
      }
    }' -f ownerId="$(gh api user --jq '.node_id')" -f title="SuperPassword Development" --jq '.data.createProjectV2.projectV2.id')
    
    echo -e "${GREEN}✅ Created project: $PROJECT_ID${NC}"
fi

echo -e "${YELLOW}📋 Syncing issues to board...${NC}"

# Get all open issues
ISSUES=$(gh issue list --state open --json number,title,labels,id --limit 100)

# Get field IDs
echo -e "${YELLOW}🔧 Getting field configuration...${NC}"
FIELDS=$(get_field_ids "$PROJECT_ID")

# Find Status field
STATUS_FIELD_ID=$(echo "$FIELDS" | jq -r '.[] | select(.name == "Status") | .id')

if [ -z "$STATUS_FIELD_ID" ]; then
    echo -e "${YELLOW}Creating Status field...${NC}"
    # Create Status field with options
    STATUS_FIELD_ID=$(gh api graphql -f query='
    mutation($projectId: ID!) {
      createProjectV2Field(input: {
        projectId: $projectId,
        dataType: SINGLE_SELECT,
        name: "Status",
        singleSelectOptions: [
          {name: "📥 Backlog", color: GRAY},
          {name: "🎯 Ready", color: YELLOW},
          {name: "🤖 AI Working", color: BLUE},
          {name: "👀 Review", color: PURPLE},
          {name: "✅ Testing", color: ORANGE},
          {name: "🚀 Done", color: GREEN}
        ]
      }) {
        projectV2Field {
          ... on ProjectV2SingleSelectField {
            id
            options {
              id
              name
            }
          }
        }
      }
    }' -f projectId="$PROJECT_ID" --jq '.data.createProjectV2Field.projectV2Field.id')
fi

# Process each issue
echo "$ISSUES" | jq -c '.[]' | while read -r issue; do
    ISSUE_NUMBER=$(echo "$issue" | jq -r '.number')
    ISSUE_TITLE=$(echo "$issue" | jq -r '.title')
    ISSUE_ID=$(echo "$issue" | jq -r '.id')
    LABELS=$(echo "$issue" | jq -r '.labels[].name' | tr '\n' ',')
    
    echo -e "\n${BLUE}Processing #$ISSUE_NUMBER: $ISSUE_TITLE${NC}"
    
    # Add to project
    ITEM_ID=$(add_issue_to_project "$PROJECT_ID" "$ISSUE_ID" 2>/dev/null || echo "")
    
    if [ -z "$ITEM_ID" ]; then
        echo "  Already in project, finding item..."
        # Find existing item
        ITEM_ID=$(gh api graphql -f query='
        query($projectId: ID!, $contentId: ID!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              items(first: 100) {
                nodes {
                  id
                  content {
                    ... on Issue {
                      id
                    }
                  }
                }
              }
            }
          }
        }' -f projectId="$PROJECT_ID" -f contentId="$ISSUE_ID" | \
        jq -r --arg id "$ISSUE_ID" '.data.node.items.nodes[] | select(.content.id == $id) | .id')
    fi
    
    if [ ! -z "$ITEM_ID" ]; then
        # Determine status based on labels
        STATUS="📥 Backlog"
        
        if [[ "$LABELS" == *"ai:completed"* ]]; then
            STATUS="🚀 Done"
        elif [[ "$LABELS" == *"ai:review-needed"* ]]; then
            STATUS="👀 Review"
        elif [[ "$LABELS" == *"ai:in-progress"* ]]; then
            STATUS="🤖 AI Working"
        elif [[ "$LABELS" == *"ai:ready"* ]]; then
            STATUS="🎯 Ready"
        fi
        
        echo "  Status: $STATUS"
        
        # Get option ID for status
        OPTION_ID=$(echo "$FIELDS" | jq -r --arg status "$STATUS" '.[] | select(.name == "Status") | .options[] | select(.name == $status) | .id')
        
        if [ ! -z "$OPTION_ID" ] && [ ! -z "$STATUS_FIELD_ID" ]; then
            update_issue_status "$PROJECT_ID" "$ITEM_ID" "$STATUS_FIELD_ID" "$OPTION_ID" 2>/dev/null || \
                echo "  ⚠️  Could not update status"
            echo -e "  ${GREEN}✅ Updated board${NC}"
        fi
    fi
done

# Show board summary
echo -e "\n${YELLOW}📊 Board Summary:${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"

gh api graphql -f query='
query($projectId: ID!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      items(first: 100) {
        totalCount
        nodes {
          fieldValues(first: 10) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
              }
            }
          }
        }
      }
    }
  }
}' -f projectId="$PROJECT_ID" | \
jq -r '.data.node.items.nodes[].fieldValues.nodes[] | select(.name != null) | .name' | \
sort | uniq -c | while read count status; do
    echo -e "  $status: ${GREEN}$count${NC}"
done

echo -e "\n${GREEN}✨ Kanban board synced successfully!${NC}"
echo -e "\n${YELLOW}View your board:${NC}"
echo -e "${BLUE}https://github.com/users/$OWNER/projects/$PROJECT_NUMBER${NC}"
