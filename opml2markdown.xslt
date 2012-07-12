<?xml version='1.0' encoding='utf-8'?>

<!-- OPML-to-Markdown converter by Fletcher Penney -->

<!-- 
# Copyright (C) 2005  Fletcher T. Penney <fletcher@freeshell.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
#    Free Software Foundation, Inc.
#    59 Temple Place, Suite 330
#    Boston, MA 02111-1307 USA
-->

<!-- To Do:
	Handle checkboxes?  Parse only checked/indeterminate?  Have a meta-option?
	Could check to see if any are checked, if so then parse checked/indet?
	Tabs get turned into spaces, ruining codeblocks
-->

<xsl:stylesheet
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	version="1.0">
	
	<xsl:output method='text' encoding='utf-8'/>

	<xsl:strip-space elements="*" />

	<xsl:variable name="newline">
<xsl:text>
</xsl:text>
	</xsl:variable>

	<xsl:variable name="tab">
<xsl:text>	</xsl:text>
	</xsl:variable>
	
	<xsl:param name="header"/>

	<xsl:template match="/">
		<xsl:apply-templates select="/opml/body/outline[last()]" mode="meta"/>
		<xsl:apply-templates select="node()">
			<!-- grr. i'm trying to sort by the outline.text attribute. why
			     doesn't this work? see http://w3schools.com/xsl/el_sort.asp
			 -->
			<xsl:sort select="@text" />
			<xsl:with-param name="header" select="concat($header,'#')"/>
		</xsl:apply-templates>
	</xsl:template>
	
	<xsl:template match="outline" mode="metadata">
		<xsl:value-of select="@text"/>
		<xsl:text>:</xsl:text>
		<xsl:value-of select="@_note"/>
		<xsl:value-of select="$newline"/>
		<xsl:apply-templates select="node()" mode="metadata"/>
	</xsl:template>

	<xsl:template match="outline" mode="meta">
			<xsl:if test="translate(@text,'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
			'abcdefghijklmnopqrstuvwxyz') = 'metadata'">
				<xsl:apply-templates select="outline" mode="metadata"/>
				<xsl:value-of select="$newline"/>
			</xsl:if>
	</xsl:template>
	
	<xsl:template match="outline">
		<xsl:if test="not(translate(@text,'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
		'abcdefghijklmnopqrstuvwxyz') = 'metadata')">
			<xsl:value-of select="concat($header,'* ')"/>
			<!-- if there's a web URL, link to it -->
			<xsl:if test = "@htmlUrl != ''">
				<xsl:text>[</xsl:text>
			</xsl:if>
			<xsl:value-of select="@text"/>
			<xsl:if test = "@htmlUrl != ''">
				<xsl:text>](</xsl:text>
				<xsl:value-of select="@htmlUrl"/>
				<xsl:text>)</xsl:text>
			</xsl:if>
			<!-- same if there's an XML URL -->
			<xsl:if test = "@xmlUrl != ''">
				<xsl:value-of select="$newline"/>
				<xsl:text>(_[subscribe](</xsl:text>
				<xsl:value-of select="@xmlUrl"/>
				<xsl:text>)_)</xsl:text>
			</xsl:if>
			<xsl:value-of select="concat(' ',$header)"/>
			<xsl:value-of select="$newline"/>
			<xsl:value-of select="$newline"/>
			<xsl:if test = "@_note">
				<xsl:value-of select="@_note"/>
				<xsl:value-of select="$newline"/>
				<xsl:value-of select="$newline"/>
			</xsl:if>
			<xsl:apply-templates select="node()">
				<xsl:with-param name="header" select="concat($header, '#')"/>
			</xsl:apply-templates>
		</xsl:if>
	</xsl:template>

	<xsl:template match="head">
		<!-- ignore header -->
	</xsl:template>

	<!-- replace-substring routine by Doug Tidwell - XSLT, O'Reilly Media -->
	<xsl:template name="replace-substring">
		<xsl:param name="original" />
		<xsl:param name="substring" />
		<xsl:param name="replacement" select="''"/>
		<xsl:variable name="first">
			<xsl:choose>
				<xsl:when test="contains($original, $substring)" >
					<xsl:value-of select="substring-before($original, $substring)"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="$original"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="middle">
			<xsl:choose>
				<xsl:when test="contains($original, $substring)" >
					<xsl:value-of select="$replacement"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:text></xsl:text>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="last">
			<xsl:choose>
				<xsl:when test="contains($original, $substring)">
					<xsl:choose>
						<xsl:when test="contains(substring-after($original, $substring), $substring)">
							<xsl:call-template name="replace-substring">
								<xsl:with-param name="original">
									<xsl:value-of select="substring-after($original, $substring)" />
								</xsl:with-param>
								<xsl:with-param name="substring">
									<xsl:value-of select="$substring" />
								</xsl:with-param>
								<xsl:with-param name="replacement">
									<xsl:value-of select="$replacement" />
								</xsl:with-param>
							</xsl:call-template>
						</xsl:when>	
						<xsl:otherwise>
							<xsl:value-of select="substring-after($original, $substring)"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:when>
				<xsl:otherwise>
					<xsl:text></xsl:text>
				</xsl:otherwise>		
			</xsl:choose>				
		</xsl:variable>		
		<xsl:value-of select="concat($first, $middle, $last)"/>
	</xsl:template>
	
</xsl:stylesheet>
